"""Typed access to XXF field values."""

from __future__ import annotations

import datetime
import struct

from pdf2xxf.codec import Packet, XxfError

ENCODING = "cp1253"
EPOCH = datetime.datetime(1, 1, 1)  # dates are milliseconds since 0001-01-01

TYPE_STRING = 1
TYPE_STRING_WIDE = 513
TYPE_SMALLINT = 2
TYPE_INTEGER = 3
TYPE_DOUBLE = 6
TYPE_DATETIME = 11

STRING_TYPES = (TYPE_STRING, TYPE_STRING_WIDE)
INT_TYPES = (TYPE_SMALLINT, TYPE_INTEGER)


def decode(field_type: int, raw: bytes):
    if not raw:
        return None
    if field_type in STRING_TYPES:
        return raw.decode(ENCODING, "replace")
    if field_type in INT_TYPES:
        return int.from_bytes(raw, "little", signed=True)
    if field_type == TYPE_DOUBLE:
        return struct.unpack("<d", raw)[0]
    if field_type == TYPE_DATETIME:
        return EPOCH + datetime.timedelta(milliseconds=struct.unpack("<d", raw)[0])
    return raw


def encode(field_type: int, size: int, value) -> bytes:
    if value is None:
        return b""
    if field_type in STRING_TYPES:
        raw = str(value).encode(ENCODING)
        if len(raw) > size:
            raise XxfError(f"value {value!r} exceeds field size {size}")
        return raw
    if field_type in INT_TYPES:
        return int(value).to_bytes(size, "little", signed=True)
    if field_type == TYPE_DOUBLE:
        return struct.pack("<d", float(value))
    if field_type == TYPE_DATETIME:
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            value = datetime.datetime.combine(value, datetime.time())
        delta = value - EPOCH
        return struct.pack("<d", float(delta // datetime.timedelta(milliseconds=1)))
    raise XxfError(f"unsupported field type {field_type}")


def get(packet: Packet, row: int, name: str):
    i = packet.index(name)
    return decode(packet.fields[i].type, packet.records[row].values[i])


def put(packet: Packet, row: int, name: str, value) -> None:
    i = packet.index(name)
    f = packet.fields[i]
    packet.records[row].values[i] = encode(f.type, f.size, value)


def dump(packet: Packet, row: int) -> dict:
    record = packet.records[row]
    return {
        f.name: decode(f.type, v)
        for f, v in zip(packet.fields, record.values, strict=True)
        if v
    }
