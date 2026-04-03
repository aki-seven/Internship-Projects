import argparse, sys, os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad   # FIX: moved unpad here

def validate_file_path(file_path: str) -> bool:
    try:
        with open(file_path, 'rb'):
            return True
    except FileNotFoundError:
        return False
        
class cli:

    def parse_arguments(self):
        usage = "%(prog)s -e <encrypt> | -d <decrypt> (-f <file_path> -k <key_path>)"
        parser = argparse.ArgumentParser(usage=usage)
        parser.add_argument("-e", "--encrypt", action="store_true")
        parser.add_argument("-d", "--decrypt", action="store_true")
        parser.add_argument("-f", "--file", dest="file_path")
        parser.add_argument("-k", "--key", dest="key_path")
        parser.add_argument("-m", "--mode", dest="mode")

        options = parser.parse_args()

        if options.encrypt == options.decrypt:
            parser.print_help()
            print("[-] Choose either -e or -d")
            sys.exit(1)

        if not options.file_path or not options.key_path or not options.mode:
            parser.print_help()
            print("[-] Missing arguments")
            sys.exit(1)

        # FIX: convert mode to int
        options.mode = int(options.mode)

        # FIX: correct validation
        if options.mode not in (1, 2, 3):
            print("[-] Error: Mode not defined.")
            sys.exit(1)

        return options

    def run_cli(self, options):

        if options.encrypt:
            enc = encryptFile()

            if options.mode == 2:   # FIX: CBC = 2
                enc.encrypt_cbc(options.key_path, options.file_path)
            else:                  # default → GCM
                enc.encrypt(options.key_path, options.file_path)

        elif options.decrypt:
            dec = decryptFile()

            if options.mode == 2:  # FIX: CBC = 2
                dec.decrypt_cbc(options.key_path, options.file_path)
            else:
                dec.decrypt(options.key_path, options.file_path)


class encryptFile:

    def encrypt(self, key_path, file_path):
        key = get_random_bytes(32)

        if not validate_file_path(file_path):
            raise FileNotFoundError("File not found: " + file_path)

        key_dir = os.path.dirname(key_path)
        if key_dir and not os.path.exists(key_dir):
            raise FileNotFoundError("Invalid key directory: " + key_dir)

        # FIX: correct mode
        cipher = AES.new(key, AES.MODE_GCM)

        with open(file_path, 'rb') as f:
            plaintext = f.read()

        ciphertext, tag = cipher.encrypt_and_digest(plaintext)

        with open(file_path + ".aes", 'wb') as f:
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)

        with open(key_path, 'wb') as f:
            f.write(key)

        print("Encrypted file saved as:", file_path + ".aes")


    # FIX: added self
    def encrypt_cbc(self, key_path, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError("File not found: " + file_path)

        key = get_random_bytes(32)
        cipher = AES.new(key, AES.MODE_CBC)

        with open(file_path, 'rb') as f:
            plaintext = f.read()

        ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))

        with open(file_path + ".cbc", 'wb') as f:
            f.write(cipher.iv)
            f.write(ciphertext)

        with open(key_path, 'wb') as f:
            f.write(key)

        print("CBC Encrypted file saved as:", file_path + ".cbc")


class decryptFile:

    def decrypt(self, key_path, file_path):

        if not validate_file_path(file_path):
            raise FileNotFoundError("File not found: " + file_path)

        if not validate_file_path(key_path):
            raise FileNotFoundError("Key not found: " + key_path)

        with open(key_path, "rb") as f:
            key = f.read()

        with open(file_path, "rb") as f:
            nonce, tag, ciphertext = [f.read(x) for x in (16, 16, -1)]

        cipher = AES.new(key, AES.MODE_GCM, nonce)

        try:
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
        except Exception:
            raise ValueError("Decryption failed")

        output_file = os.path.splitext(file_path)[0]

        with open(output_file, 'wb') as f:
            f.write(plaintext)

        print("Decrypted file saved as:", output_file)


    # FIX: added self
    def decrypt_cbc(self, key_path, file_path):
        if not os.path.isfile(file_path):
            raise FileNotFoundError("File not found: " + file_path)

        if not os.path.isfile(key_path):
            raise FileNotFoundError("Key not found: " + key_path)

        with open(key_path, 'rb') as f:
            key = f.read()

        with open(file_path, 'rb') as f:
            iv = f.read(16)
            ciphertext = f.read()

        cipher = AES.new(key, AES.MODE_CBC, iv)

        try:
            plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        except ValueError:
            raise ValueError("Decryption failed")

        output_file = os.path.splitext(file_path)[0]

        with open(output_file, 'wb') as f:
            f.write(plaintext)

        print("Decrypted file saved as:", output_file)


initialize = cli()
args = initialize.parse_arguments()
initialize.run_cli(args)