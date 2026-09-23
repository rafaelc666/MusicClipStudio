"""Verifica portas TCP e mostra processos donos."""
import os
import sys
import socket
import ctypes
import ctypes.wintypes
from pathlib import Path

# Garante UTF-8 no Windows terminal, fallback silencioso
PY37 = sys.version_info >= (3, 7)
if os.name == "nt" and PY37:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# MIB_TCPROW_OWNER_PID / MIB_TCPTABLE_OWNER_PID
class MIB_TCPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [
        ("dwState",      ctypes.wintypes.DWORD),
        ("dwLocalAddr",  ctypes.wintypes.DWORD),
        ("dwLocalPort",  ctypes.wintypes.DWORD),  # network byte order
        ("dwRemoteAddr", ctypes.wintypes.DWORD),
        ("dwRemotePort", ctypes.wintypes.DWORD),
        ("dwOwningPid",  ctypes.wintypes.DWORD),
    ]

def _ntohs(x: int) -> int:
    return ((x & 0xff) << 8) | ((x >> 8) & 0xff)

def get_tcp_listeners():
    """Retorna dict: porta_local -> pid (apenas Listening, IPv4)."""
    iphlpapi = ctypes.windll.iphlpapi
    buf = ctypes.create_string_buffer(0)
    size = ctypes.wintypes.DWORD(0)
    # Primeira chamada para saber o tamanho
    ret = iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(size), False, 2, 5, 0)
    if ret != 122 and ret != 0:  # ERROR_INSUFFICIENT_BUFFER ou sucesso
        return {}
    buf = ctypes.create_string_buffer(size.value)
    ret = iphlpapi.GetExtendedTcpTable(buf, ctypes.byref(size), False, 2, 5, 0)
    if ret != 0:
        return {}
    n = ctypes.wintypes.DWORD.from_buffer_copy(buf[:4]).value
    rows = (MIB_TCPROW_OWNER_PID * n).from_buffer_copy(buf[4:])
    result = {}
    for r in rows:
        # MIB_TCP_STATE_LISTEN = 2
        if r.dwState == 2:
            port = _ntohs(r.dwLocalPort)
            # Filtrar 127.0.0.1 (dwLocalAddr = 0x0100007F = 127.0.0.1 little-endian)
            # Para checar TUDO (0.0.0.0 + 127.0.0.1), ignoramos o filtro aqui:
            if r.dwLocalAddr in (0x0100007F, 0):  # 127.0.0.1 ou 0.0.0.0
                result[port] = r.dwOwningPid
    return result

def process_name(pid: int) -> str:
    try:
        import psutil
        p = psutil.Process(pid)
        return f"{p.name()} (pid={pid}) · {getattr(p, 'exe', lambda: '')() or ''}"
    except Exception:
        # Fallback: lê via kernel32 (só nome do executável na maioria dos casos)
        PROCESS_QUERY_INFORMATION = 0x0400
        PROCESS_VM_READ = 0x0010
        k32 = ctypes.windll.kernel32
        h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            return f"(pid={pid} - sem acesso)"
        try:
            name_buf = ctypes.create_unicode_buffer(260)
            nsize = ctypes.wintypes.DWORD(260)
            ok = ctypes.windll.psapi.GetProcessImageFileNameW(h, name_buf, ctypes.byref(nsize))
            if ok:
                name = Path(name_buf.value).name if name_buf.value else ""
                return f"{name} (pid={pid})"
            return f"(pid={pid})"
        finally:
            k32.CloseHandle(h)

def check(port: int, listeners: dict) -> None:
    pid = listeners.get(port)
    if pid is None:
        print(f"[ LIVRE  ] :{port:>5}")
    else:
        print(f"[OCUPADA] :{port:>5}  <- {process_name(pid)}")

def main():
    print("=" * 60)
    print("  MusicClipStudio WEB · Verificador de portas")
    print("=" * 60)
    listeners = get_tcp_listeners()

    check_targets = [3100, 8300, 3000, 3690, 8000, 3001, 5173, 8080, 4200]
    print("\n▶ Portas alvo (front/back/etc.):")
    for p in check_targets:
        check(p, listeners)

    print("\n▶ Todas as portas localhost / 0.0.0.0 em LISTENING (ordenadas):")
    for p in sorted(listeners.keys()):
        print(f"    :{p:>5}  <- {process_name(listeners[p])}")

if __name__ == "__main__":
    main()
