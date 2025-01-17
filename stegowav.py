#!/usr/bin/python3

import argparse
from pathlib import Path
import cProfile

from error_correction.error_correction_provider import ErrorCorrectionProvider
from error_correction.error_correction_type import ErrorCorrectionType
from matplotlib import pyplot as plt

from security.encryption_provider import EncryptionProvider
from security.enums.encryption_type import EncryptionType
from security.enums.hash_type import HashType
from wav_steganography.wav_file import WAVFile


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Encode message into a WAV file.")
    parser.add_argument("input", type=str, help="input file path")
    parser.add_argument("-o", "--output", type=str, help="output file path to be written to")
    parser.add_argument("-e", "--encode", type=str, help="encode given text message into wav file")
    parser.add_argument("-d", "--decode", action="store_true", help="decode a text message from wav file if possible")

    parser.add_argument("--overwrite", action="store_true",
                        help="if the file specified as output should be overwritten")

    possible_encryption_values = ', '.join(f"{enc.value}: {enc.name}" for enc in EncryptionType)
    parser.add_argument("-t", "--encryption_type", type=int, default=EncryptionType.NONE,
                        help=f"encryption type as number to use ({possible_encryption_values}). "
                             f"Certain encryptors require certain hashes!")

    possible_hash_values = ', '.join(f"{ht.value}: {ht.name}" for ht in HashType)
    parser.add_argument("-a", "--hash_type", type=int, default=HashType.PBKDF2,
                        help=f"hash type as number to use ({possible_hash_values})")

    error_correction_type_values = ', '.join(f"{ect.value}: {ect.name}" for ect in ErrorCorrectionType)
    parser.add_argument("-c", "--error_correction_type", type = int, default = 2,
                        help = f"error correction type as number to use ({error_correction_type_values})")

    parser.add_argument("-r", "--redundant_bits", type=int, default=0,
                        help="number of redundant bits for error correction")

    parser.add_argument("-l", "--lsb", type=int, default=2,
                        help="number of least significant bits to use while encoding")

    parser.add_argument("--use_nth_byte", type=int, default=1,
                        help="use only every nth byte (e.g. if 4: 1 byte will be used for data, 3 will be skipped)")

    parser.add_argument("-f", "--fill", action="store_true", help="fill entire file by repeating data")

    parser.add_argument("--profile", action="store_true", help="profile code (show which parts are taking long)")

    parser.add_argument("-s", "--spectrogram", action="store_true", help="display a spectrogram of the given file")

    parser.add_argument("-p", "--play", action="store_true",
                        help="play the file (if -e provided, it will play after encoding, to hear the noise)")

    return parser.parse_args()


def handle_args(args):

    encryption_type = EncryptionType(args.encryption_type)
    hash_type = HashType(args.hash_type)
    error_correction_type = ErrorCorrectionType(args.error_correction_type)

    if error_correction_type == ErrorCorrectionType.HAMMING or error_correction_type == ErrorCorrectionType.NONE:
        print('WARNING: If you choose to use no or hamming error correction when encoding '
              'you MUST use the same error correction type during decoding!')

    audio_path = Path(__file__).parent.parent / "audio"

    audio_file_keywords = {
        "sine": audio_path / "sine_mono_110hz.wav",
        "square": audio_path / "square_stereo_110hz.wav",
        "sawtooth": audio_path / "sawtooth_mono_220hz.wav",
        "hello": audio_path / "voice_hello.wav",
    }
    if args.input in audio_file_keywords:
        args.input = audio_file_keywords[args.input]

    wav_file = WAVFile(args.input)

    encryptor = EncryptionProvider.get_encryptor(encryption_type, hash_type, decryption=args.decode)
    error_correction = ErrorCorrectionProvider.get_error_correction(error_correction_type=error_correction_type)

    post_encoding_spectrum_ax, diff_ax = None, None
    if args.encode:
        if args.spectrogram:
            # Add diff_ax if difference is wanted
            fig, (pre_encoding_spectrum_ax, post_encoding_spectrum_ax) = plt.subplots(2, 1)
            pre_encoding_spectrum = wav_file.spectrogram(show=False, ax=pre_encoding_spectrum_ax)
            pre_encoding_spectrum_ax.set_xlabel("")
            pre_encoding_spectrum_ax.set_title("Spectrogram before encoding")
            fig.suptitle("Comparison between pre- and post-encoding of information in WAV file")

        wav_file.encode(
            args.encode.encode("UTF-8"),
            least_significant_bits=args.lsb,
            every_nth_byte=args.use_nth_byte,
            redundant_bits=args.redundant_bits,
            encryptor=encryptor,
            error_correction=error_correction,
            repeat_data=args.fill,
        )

    if args.decode:
        decoded_message = wav_file.decode(encryptor=encryptor)

        decoded_string = decoded_message.decode("UTF-8")

        print(f"Decoded message (len={len(decoded_string)}):")
        print(decoded_string)

    if args.spectrogram:
        if post_encoding_spectrum_ax is None:
            fig, axes = plt.subplots()
            post_encoding_spectrum_ax = axes
        else:
            post_encoding_spectrum_ax.set_title("Spectrogram after encoding")
        post_encoding_spectrum = wav_file.spectrogram(show=False, ax=post_encoding_spectrum_ax)
        if diff_ax is not None:
            diff_ax.pcolormesh(post_encoding_spectrum - pre_encoding_spectrum, vmax=.1)
            diff_ax.set_yticks([])
            diff_ax.set_xticks([])
            diff_ax.set_title("Difference")

        plt.show()

    if args.output:
        wav_file.write(Path(args.output), overwrite=args.overwrite)
        print(f"Written to {args.output}!")

    if args.play:
        wav_file.play()


def main():
    args = parse_arguments()
    if args.profile:
        with cProfile.Profile() as pr:
            handle_args(args)
        pr.print_stats()
    else:
        handle_args(args)


if __name__ == "__main__":
    main()
