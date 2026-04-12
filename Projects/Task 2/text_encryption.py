from Crypto.Cipher import AES
import base64

encryption_key = b'This_key_is_32_bytes_long!123456'

def encrypt(plaintext):
    cipher = AES.new(encryption_key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode())

    return {
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "nonce": base64.b64encode(cipher.nonce).decode(),
        "tag": base64.b64encode(tag).decode()
        } # returning strings here

def decrypt(encrypted_text):
    cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=base64.b64decode(encrypted_text["nonce"]))
    plaintext = cipher.decrypt_and_verify(base64.b64decode(encrypted_text["ciphertext"]), base64.b64decode(encrypted_text["tag"]))
    return plaintext.decode()
