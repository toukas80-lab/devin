"""Codec for SoftOne XXF export/import files.

The format is fully self-describing:

    "SOFTONE EXPORT\\0" + 13 header bytes
    repeated sections:
        u8 name length, name, u32 packet count
        repeated packets:
            u32 packet size, then the packet itself:
                "XSF_", u16 version, u16 flags, u8 name length, name
                if flags == 6:   u32 field-table size, u16 field count,
                                 field defs (u16 type, u16 size, u16 offset,
                                 u16 kind, NUL-terminated name)
                records:         u8 0x00, u32 row number,
                                 one length-prefixed value per field
                                 (length 0 means NULL)

Packets with flags != 6 reuse the field table of the previous packet with the
same name, so schemas are tracked while reading.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from dataclasses import field as dc_field

MAGIC = b"SOFTONE EXPORT\x00"
HEADER_SIZE = 28
FLAG_WITH_SCHEMA = 6

TYPE_STRING = 1
TYPE_SMALLINT = 2
TYPE_INTEGER = 3
TYPE_FLOAT = 8
TYPE_DATETIME = 11


class XxfError(Exception):
    pass


@dataclass
class FieldDef:
    name: str
    type: int
    size: int
    offset: int
    kind: int


@dataclass
class Record:
    row: int
    values: list[bytes]


@dataclass
class Packet:
    name: str
    version: int
    flags: int
    fields: list[FieldDef]
    records: list[Record] = dc_field(default_factory=list)

    def index(self, field_name: str) -> int:
        for i, f in enumerate(self.fields):
            if f.name == field_name:
                return i
        raise XxfError(f"{self.name}: unknown field {field_name}")


@dataclass
class Section:
    name: str
    packets: list[Packet]


@dataclass
class Document:
    header: bytes
    sections: list[Section]

    def packets(self, name: str) -> list[Packet]:
        return [p for s in self.sections for p in s.packets if p.name == name]

    def packet(self, name: str) -> Packet:
        found = self.packets(name)
        if len(found) != 1:
            raise XxfError(f"expected exactly one {name}, found {len(found)}")
        return found[0]


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def bytes(self, n: int) -> bytes:
        out = self.data[self.pos : self.pos + n]
        if len(out) != n:
            raise XxfError("unexpected end of file")
        self.pos += n
        return out

    def u8(self) -> int:
        return self.bytes(1)[0]

    def u16(self) -> int:
        return struct.unpack("<H", self.bytes(2))[0]

    def u32(self) -> int:
        return struct.unpack("<I", self.bytes(4))[0]

    def name(self) -> str:
        return self.bytes(self.u8()).decode("latin1")

    def cstring(self) -> str:
        end = self.data.index(b"\x00", self.pos)
        out = self.data[self.pos : end].decode("latin1")
        self.pos = end + 1
        return out


def parse(data: bytes) -> Document:
    if not data.startswith(MAGIC):
        raise XxfError("not a SoftOne XXF file")
    r = _Reader(data)
    header = r.bytes(HEADER_SIZE)
    schemas: dict[str, list[FieldDef]] = {}
    sections: list[Section] = []
    while r.pos < len(data):
        section_name = r.name()
        packets = [_parse_packet(r, schemas) for _ in range(r.u32())]
        sections.append(Section(section_name, packets))
    return Document(header, sections)


def _parse_packet(r: _Reader, schemas: dict[str, list[FieldDef]]) -> Packet:
    size = r.u32()
    end = r.pos + size
    if r.bytes(4) != b"XSF_":
        raise XxfError("missing XSF_ packet marker")
    version = r.u16()
    flags = r.u16()
    name = r.name()
    if flags == FLAG_WITH_SCHEMA:
        r.u32()  # field table size, recomputed on write
        fields = []
        for _ in range(r.u16()):
            ftype, fsize, foffset, fkind = struct.unpack("<HHHH", r.bytes(8))
            fields.append(FieldDef(r.cstring(), ftype, fsize, foffset, fkind))
        schemas[name] = fields
    else:
        if name not in schemas:
            raise XxfError(f"{name}: schema-less packet before its schema")
        fields = schemas[name]
    records = []
    while r.pos < end:
        if r.u8() != 0:
            raise XxfError(f"{name}: bad record marker")
        row = r.u32()
        records.append(Record(row, [r.bytes(r.u8()) for _ in fields]))
    if r.pos != end:
        raise XxfError(f"{name}: record data overruns the packet")
    return Packet(name, version, flags, fields, records)


def serialize(doc: Document) -> bytes:
    out = bytearray(doc.header)
    for section in doc.sections:
        name = section.name.encode("latin1")
        out += bytes([len(name)]) + name
        out += struct.pack("<I", len(section.packets))
        for packet in section.packets:
            body = _serialize_packet(packet)
            out += struct.pack("<I", len(body)) + body
    return bytes(out)


def _serialize_packet(packet: Packet) -> bytes:
    name = packet.name.encode("latin1")
    out = bytearray(b"XSF_")
    out += struct.pack("<HH", packet.version, packet.flags)
    out += bytes([len(name)]) + name
    if packet.flags == FLAG_WITH_SCHEMA:
        table = bytearray(struct.pack("<H", len(packet.fields)))
        for f in packet.fields:
            table += struct.pack("<HHHH", f.type, f.size, f.offset, f.kind)
            table += f.name.encode("latin1") + b"\x00"
        out += struct.pack("<I", len(table)) + table
    for record in packet.records:
        out += b"\x00" + struct.pack("<I", record.row)
        for value in record.values:
            if len(value) > 255:
                raise XxfError(f"{packet.name}: value longer than 255 bytes")
            out += bytes([len(value)]) + value
    return bytes(out)
