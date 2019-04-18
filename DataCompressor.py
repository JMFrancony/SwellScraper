# !/usr/bin/env python
# -*- coding: utf-8 -*-

''' used to compress data
'''
import zlib
import json
from pprint import pprint

# ============================================================================================================
class BinaryCompressor:
    # Compress string data into binary object using zlib
    @staticmethod
    def compress(data_to_compress):
        compressed_data = zlib.compress(data_to_compress.encode('utf-8'))
        return compressed_data


class BinaryDecompressor:
    # Decompress data from binary to string using zlib
    @staticmethod
    def decompress(data_to_decompress):
        decompressed_data = zlib.decompress(data_to_decompress)
        return decompressed_data.decode('utf-8')


if __name__ == '__main__':
    with open('output.jsonl') as json_data:
        d = json.load(json_data)
        pprint(d)
        d_mod = d['dom_tree']
        d_mod_comp = BinaryCompressor.compress(json.dumps(d_mod))
        print(json.dumps(d_mod))
        d_mod_decomp = BinaryDecompressor.decompress(d_mod_comp)
        print(d_mod_decomp)







