from __future__ import annotations

import platform
from dataclasses import dataclass


class CredentialStoreError(RuntimeError):
    pass


@dataclass(frozen=True)
class WindowsCredential:
    username: str
    password: str


if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes

    _CRED_TYPE_GENERIC = 1
    _CRED_PERSIST_LOCAL_MACHINE = 2

    class _CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", wintypes.FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(wintypes.BYTE)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    _PCREDENTIALW = ctypes.POINTER(_CREDENTIALW)
    _advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    _advapi32.CredReadW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(_PCREDENTIALW),
    ]
    _advapi32.CredReadW.restype = wintypes.BOOL
    _advapi32.CredWriteW.argtypes = [
        ctypes.POINTER(_CREDENTIALW),
        wintypes.DWORD,
    ]
    _advapi32.CredWriteW.restype = wintypes.BOOL
    _advapi32.CredFree.argtypes = [ctypes.c_void_p]
    _advapi32.CredFree.restype = None


def read_windows_credential(target: str) -> WindowsCredential:
    if platform.system() != "Windows":
        raise CredentialStoreError("Το Windows Credential Manager απαιτεί Windows")

    pointer = _PCREDENTIALW()
    if not _advapi32.CredReadW(target, _CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        error = ctypes.get_last_error()
        raise CredentialStoreError(
            f"Δεν βρέθηκαν αποθηκευμένα στοιχεία SoftOne ({error})"
        )
    try:
        credential = pointer.contents
        password_bytes = ctypes.string_at(
            credential.CredentialBlob,
            credential.CredentialBlobSize,
        )
        return WindowsCredential(
            username=credential.UserName or "",
            password=password_bytes.decode("utf-16-le"),
        )
    finally:
        _advapi32.CredFree(pointer)


def write_windows_credential(target: str, username: str, password: str) -> None:
    if platform.system() != "Windows":
        raise CredentialStoreError("Το Windows Credential Manager απαιτεί Windows")
    if not target or not username or not password:
        raise CredentialStoreError("Target, username και password είναι υποχρεωτικά")

    password_bytes = password.encode("utf-16-le")
    buffer = ctypes.create_string_buffer(password_bytes)
    credential = _CREDENTIALW()
    credential.Type = _CRED_TYPE_GENERIC
    credential.TargetName = target
    credential.CredentialBlobSize = len(password_bytes)
    credential.CredentialBlob = ctypes.cast(
        buffer,
        ctypes.POINTER(wintypes.BYTE),
    )
    credential.Persist = _CRED_PERSIST_LOCAL_MACHINE
    credential.UserName = username

    if not _advapi32.CredWriteW(ctypes.byref(credential), 0):
        error = ctypes.get_last_error()
        raise CredentialStoreError(
            f"Δεν αποθηκεύτηκαν τα στοιχεία στο Credential Manager ({error})"
        )
