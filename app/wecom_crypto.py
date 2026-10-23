import base64
import hashlib
import json
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class WeComCrypto:
    def __init__(self, token: str, encoding_aes_key: str):
        self.token = token
        self.key = base64.b64decode(encoding_aes_key + "=")
        if len(self.key) != 32:
            raise ValueError("WECOM_ENCODING_AES_KEY 必须是企业微信提供的 43 位密钥")

    def signature(self, timestamp: str, nonce: str, encrypted: str) -> str:
        return hashlib.sha1("".join(sorted((self.token, timestamp, nonce, encrypted))).encode()).hexdigest()

    def verify(self, signature: str, timestamp: str, nonce: str, encrypted: str) -> bool:
        return signature == self.signature(timestamp, nonce, encrypted)

    def decrypt(self, encrypted: str) -> str:
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.key[:16]))
        decryptor = cipher.decryptor()
        padded = decryptor.update(base64.b64decode(encrypted)) + decryptor.finalize()
        pad = padded[-1]
        if pad < 1 or pad > 32:
            raise ValueError("企业微信消息填充无效")
        plain = padded[:-pad]
        message_length = struct.unpack("!I", plain[16:20])[0]
        return plain[20:20 + message_length].decode("utf-8")

    def decrypt_json(self, encrypted: str) -> dict:
        return json.loads(self.decrypt(encrypted))
