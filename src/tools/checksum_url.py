
import hashlib
from re import finditer

import requests
import sys


def test_hash_length():
    m = hashlib.md5()
    m.update(b'wibble')
    return len(m.hexdigest())

def exception_to_message(exception):
    identifier =  exception.__class__.__name__
    matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    camels = [match.group(0).lower() for match in matches]
    return ' '.join(camels)

if __name__ == '__main__':
    for url in sys.argv[1:]:
        try:
            response = requests.get(url, allow_redirects=True, timeout=10, stream=True)
            total_length = response.headers.get('content-length')

            m = hashlib.md5()

            m_length = test_hash_length()

            data = None
            if response.status_code != 200:
                sys.stdout.write(f"{url} : download failed [response was {response.status_code}]")
            elif total_length is None:  # no content length header
                m.update(response.content)
            else:
                try:
                    dl = 0
                    total_length = int(total_length)
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        m.update(data)
                        done = int(m_length * dl / total_length)
                        sys.stdout.write(f"\r{url} : [%s%s]  " % ('=' * done, ' ' * (m_length - done)))
                        sys.stdout.flush()
                    sys.stdout.write(f"\r{url} : {m.hexdigest()}")
                except Exception as e:
                    sys.stdout.write(f"\r{url} : download failed [{exception_to_message(e)}]")

            print()
        except Exception as e:
            sys.stdout.write(f"\r{url} : download failed [{exception_to_message(e)}]")

