#!/usr/bin/env python3

# Package imports
from dotenv import load_dotenv
import binascii
import os

load_dotenv()  # take environment variables from .env


class AuxProcessing:

    @staticmethod
    def IntegersToBinary(integer_representation) -> str:
        '''This assumes that each integer in the integer representation should be representated as 4 bits, that is, '0' in dec is '0000' in binary, even though '0' can also be used. This is done so for ease of parsing here'''
        return str(''.join([((int(os.environ['ENTRY_LENGTH']) - len(bin_value)) * '0') + bin_value for bin_value in [bin(int(character))[2:] for character in str(integer_representation)]]))

    @staticmethod
    def BinaryToIntegers(binary_representation) -> int:
        '''This assumes that each representation is
        split into a nibble format, that is, the number
        of bits to represent a single value consists of 4 bits, regardless of the value, from 0000 to 1111'''
        return int(''.join([str(int(binary_representation[index:index+4], 2)) for index in range(0, len(binary_representation), 4)]))

    @staticmethod
    def UTF8ToBinary(utf8_representation, encoding='utf-8', errors='surrogatepass') -> str:
        if isinstance(utf8_representation, str):
            bits = bin(int(binascii.hexlify(
                utf8_representation.encode(encoding, errors)), 16))[2:]
            return bits.zfill(8 * ((len(bits) + 7) // 8))
        else:
            try:
                bits = bin(int(binascii.hexlify(utf8_representation.decode('utf-8')), 16))[2:]
                return bits.zfill(8 * ((len(bits) + 7) // 8))
            except UnicodeDecodeError:
                print("Unable to decode the input using UTF-8. Attempting with 'latin-1' encoding.")
                try:
                    bits = bin(int(binascii.hexlify(utf8_representation.decode('latin-1')), 16))[2:]
                    return bits.zfill(8 * ((len(bits) + 7) // 8))
                except UnicodeDecodeError:
                    print("Unable to decode the input using 'latin-1' encoding. Returning an empty string.")
                    return ""


    @staticmethod
    def BinaryToUTF8(binary_representation, encoding='utf-8', errors='surrogatepass') -> str:
        return AuxProcessing.IntegerToBytes(int(binary_representation, 2)).decode(encoding, errors)

    @staticmethod
    def IntegerToBytes(integer_representation) -> bytes:
        hex_string = '%x' % integer_representation
        number = len(hex_string)
        return binascii.unhexlify(hex_string.zfill(number + (number & 1)))
