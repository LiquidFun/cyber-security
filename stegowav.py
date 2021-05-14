#!/usr/bin/python3

import argparse

from wav_steganography.wav_file import WAVFile


def main():
    parser = argparse.ArgumentParser(description="Encode message into a WAV file.")
    parser.add_argument("input", type=str, help="input file path")
    parser.add_argument("-o", "--output", type=str, help="output file path")
    parser.add_argument("--overwrite", action="store_true",
                        help="if the file specified as output should be overwritten")
    parser.add_argument("-e", "--encode", type=str, help="encode text message into wav file")
    parser.add_argument("-d", "--decode", action="store_true", help="decode text message from wav file")
    parser.add_argument("-p", "--password", type=str,
                        help="encrypt message with a password (will ask for password (TODO))")
    args = parser.parse_args()

    wav_file = WAVFile(args.input)

    if args.encode:
        wav_file.encode(args.encode.encode("UTF-8"), password=args.password)

    if args.decode:
        decoded_message = wav_file.decode(password=args.password).decode("UTF-8")
        print(f"Decoded message (len={len(decoded_message)}):")
        print(decoded_message)

    if args.output:
        wav_file.write(args.output, overwrite=args.overwrite)
        print(f"Written to {args.output}!")


if __name__ == "__main__":
    main()
