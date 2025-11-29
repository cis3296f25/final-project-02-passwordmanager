import ctypes
import atexit

def zero_bytearray_in_memory(data):
    if data is None or not isinstance(data, bytearray):
        return
    
    if len(data) > 0:
        buffer = (ctypes.c_char * len(data)).from_buffer(data)
        ctypes.memset(ctypes.addressof(buffer), 0, len(data))
        data[:] = b'\x00' * len(data)

def cleanup_secrets():
    from passwordmanager.api.routes import current_vmk, current_vmk_cipher
    
    if current_vmk is not None:
        if isinstance(current_vmk, bytearray):
            zero_bytearray_in_memory(current_vmk)
        elif isinstance(current_vmk, bytes):
            ba = bytearray(current_vmk)
            zero_bytearray_in_memory(ba)
        
    if current_vmk_cipher is not None:
        if hasattr(current_vmk_cipher, '_signing_key') and current_vmk_cipher._signing_key is not None:
            key = current_vmk_cipher._signing_key
            ba = bytearray(key)
            zero_bytearray_in_memory(ba)
        if hasattr(current_vmk_cipher, '_encryption_key') and current_vmk_cipher._encryption_key is not None:
            key = current_vmk_cipher._encryption_key
            ba = bytearray(key)
            zero_bytearray_in_memory(ba)

atexit.register(cleanup_secrets)