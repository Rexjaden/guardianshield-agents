import hashlib
import base64
import sys
import re

def get_cert_fingerprint(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print(f"Read {len(content)} bytes from file.")
        
        # Find the first certificate block
        pattern = r"-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----"
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            print("No certificate found in file")
            return

        # Extract potential base64 part
        raw_b64 = match.group(1)
        
        # Keep ONLY valid base64 characters
        clean_b64 = re.sub(r'[^A-Za-z0-9+/]', '', raw_b64) # Remove = as well to re-pad cleanly
        
        # Fix Padding
        padding_needed = 4 - (len(clean_b64) % 4)
        if padding_needed != 4:
            clean_b64 += "=" * padding_needed
            
        print(f"Base64 length (padded): {len(clean_b64)}")
        
        # Decode
        der_data = base64.b64decode(clean_b64)
        print(f"Successfully decoded {len(der_data)} bytes of DER data.")
        
        # Hash
        sha256_fingerprint = hashlib.sha256(der_data).hexdigest().upper()
        sha1_fingerprint = hashlib.sha1(der_data).hexdigest().upper()
        
        # Format with colons
        sha256_fmt = ':'.join(sha256_fingerprint[i:i+2] for i in range(0, len(sha256_fingerprint), 2))
        sha1_fmt = ':'.join(sha1_fingerprint[i:i+2] for i in range(0, len(sha1_fingerprint), 2))
        
        print("-" * 40)
        print(f"SHA256 Fingerprint:\n{sha256_fmt}")
        print("-" * 40)
        print(f"SHA1 Fingerprint:\n{sha1_fmt}")
        print("-" * 40)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_cert_fingerprint(sys.argv[1])
    else:
        print("Usage: python script.py <cert_file>")
