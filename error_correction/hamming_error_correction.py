import numpy as np


class HammingErrorCorrection:

    @staticmethod
    def encode_hamming_error_correction(data: bytes, redundant_bits: int) -> bytes:

        hamming_code = []

        data_as_bits = HammingErrorCorrection.return_as_bits(data[::-1])

        number_of_data_and_redundant_bits = 8 + redundant_bits

        while len(data_as_bits) > 0:
            next_bits = data_as_bits[-8:]

            hamming_code_with_placeholders = \
                HammingErrorCorrection.add_placeholder_redundant_bits(next_bits, number_of_data_and_redundant_bits)

            hamming_code_calculated = \
                HammingErrorCorrection.calculate_values_for_redundant_bits(redundant_bits,
                                                                           number_of_data_and_redundant_bits,
                                                                           hamming_code_with_placeholders)

            hamming_code.extend(hamming_code_calculated)

            data_as_bits = data_as_bits[:-8]

        return b''.join(HammingErrorCorrection.convert_bits_to_bytes(hamming_code))

    @staticmethod
    def decode_hamming_error_correction(data: bytes, redundant_bits: int) -> bytes:

        decoded_hamming_code = []

        data_as_bits = HammingErrorCorrection.return_as_bits(data)

        data_as_bits = HammingErrorCorrection.add_lost_bits(data_as_bits)

        number_of_data_and_redundant_bits = 8 + redundant_bits

        while len(data_as_bits) > 0:
            next_hamming_bits = data_as_bits[:number_of_data_and_redundant_bits]

            cleaned_hamming_bits = HammingErrorCorrection.remove_all_redundant_bits(next_hamming_bits, redundant_bits)

            decoded_hamming_code.extend(cleaned_hamming_bits)

            data_as_bits = data_as_bits[number_of_data_and_redundant_bits:]

            if HammingErrorCorrection.ignore_remaining_bits(data_as_bits):
                break

        return b''.join(HammingErrorCorrection.convert_bits_to_bytes(decoded_hamming_code))

    @staticmethod
    def correct_errors_hamming(decoded_data: bytes, redundant_bits: int) -> bytes:

        corrected_data = []

        hamming_code_as_bits = HammingErrorCorrection.return_as_bits(decoded_data)

        hamming_code_as_bits = HammingErrorCorrection.add_lost_bits(hamming_code_as_bits)

        number_of_data_and_redundant_bits = 8 + redundant_bits

        while len(hamming_code_as_bits) > 0:
            next_hamming_bits = hamming_code_as_bits[:number_of_data_and_redundant_bits]

            number_of_iterations, error_syndrome = 0, []

            while number_of_iterations < redundant_bits:
                position_of_next_redundant_bit = 2 ** number_of_iterations

                sum_of_bit_values = HammingErrorCorrection.calculate_sum_of_bit_values(
                    number_of_data_and_redundant_bits,
                    position_of_next_redundant_bit,
                    next_hamming_bits)

                error_syndrome.extend([sum_of_bit_values % 2])

                number_of_iterations += 1

            # Check if a bit is flipped
            sum_of_parity_bit_values, number_of_iterations, position_of_flipped_bit = 0, 0, 0

            for value in error_syndrome:
                sum_of_parity_bit_values += value
                if value == 1:
                    position_of_flipped_bit += 2 ** number_of_iterations
                number_of_iterations += 1

            position_of_flipped_bit -= 1  # Subtract one to get the correct position in the array

            if position_of_flipped_bit < 0:
                position_of_flipped_bit = 0

            # Correct the flipped bit if there is one
            if sum_of_parity_bit_values != 0:
                if position_of_flipped_bit >= 12:
                    print("More than one flipped bit (error) found! Could not correct any bits")
                else:
                    if next_hamming_bits[position_of_flipped_bit] == 0:
                        next_hamming_bits[position_of_flipped_bit] = 1
                    else:
                        next_hamming_bits[position_of_flipped_bit] = 0

            corrected_data.extend(next_hamming_bits)

            hamming_code_as_bits = hamming_code_as_bits[number_of_data_and_redundant_bits:]

            if HammingErrorCorrection.ignore_remaining_bits(hamming_code_as_bits):
                break

        corrected_data_as_byte_string = b''.join(HammingErrorCorrection.convert_bits_to_bytes(corrected_data))

        corrected_decoded_data =\
            HammingErrorCorrection.decode_hamming_error_correction(corrected_data_as_byte_string, redundant_bits)

        return corrected_decoded_data

    @staticmethod
    def add_placeholder_redundant_bits(data_as_bits: list, number_of_data_and_redundant_bits: int) -> list:

        j, k, hamming_code_with_placeholders = 0, 0, []

        for i in range(0, number_of_data_and_redundant_bits):
            position_of_next_redundant_bit = 2 ** j

            if position_of_next_redundant_bit == i + 1:
                hamming_code_with_placeholders.append(0)
                j += 1
            else:
                hamming_code_with_placeholders.append(int(data_as_bits[k]))
                k += 1

            i += 1

        return hamming_code_with_placeholders

    @staticmethod
    def calculate_sum_of_bit_values(number_of_data_and_redundant_bits: int, position_of_next_redundant_bit: int,
                                    hamming_code: list) -> int:

        sum_of_bit_values = 0
        j = position_of_next_redundant_bit - 1

        # Check all relevant bits in the array for their value
        # https://users.cis.fiu.edu/~downeyt/cop3402/hamming.html
        while j < number_of_data_and_redundant_bits:
            for i in range(position_of_next_redundant_bit):
                sum_of_bit_values += hamming_code[j]
                j += 1
                if j >= number_of_data_and_redundant_bits:
                    break

            j += position_of_next_redundant_bit

        return sum_of_bit_values

    @staticmethod
    def calculate_values_for_redundant_bits(redundant_bits: int, number_of_data_and_redundant_bits: int,
                                            hamming_code: list) -> list:

        number_of_iterations = 0

        while number_of_iterations < redundant_bits:
            position_of_next_redundant_bit = 2 ** number_of_iterations

            sum_of_bit_values = HammingErrorCorrection.calculate_sum_of_bit_values(number_of_data_and_redundant_bits,
                                                                                   position_of_next_redundant_bit,
                                                                                   hamming_code)

            # Check if all relevant bits have an even number of 1's
            # If not, update redundant bit value for even parity
            if sum_of_bit_values % 2 != 0:
                hamming_code[position_of_next_redundant_bit - 1] = 1

            number_of_iterations += 1

        return hamming_code

    @staticmethod
    def get_bytes(bits: iter) -> bytes:

        done = False
        while not done:
            byte = 0
            for _ in range(0, 8):
                try:
                    bit = next(bits)
                except StopIteration:
                    bit = 0
                    done = True
                byte = (byte << 1) | bit
            yield byte

    @staticmethod
    def convert_bits_to_bytes(hamming_code: list) -> list:

        byte_array, number_of_iterations = [], 0

        for b in HammingErrorCorrection.get_bytes(iter(hamming_code)):
            number_of_iterations += 1
            byte_array.append(bytes([b]))

        number_of_bytes = len(hamming_code) / 8

        # Remove possible empty byte that can occur
        if number_of_bytes + 1 == number_of_iterations:
            byte_array = byte_array[:-1]

        return byte_array

    @staticmethod
    def remove_all_redundant_bits(list_of_hamming_bits: list, redundant_bits: int) -> list:

        number_of_iterations = 0

        while number_of_iterations < redundant_bits:
            position_of_next_redundant_bit = 2 ** number_of_iterations - 1 - number_of_iterations

            if position_of_next_redundant_bit < len(list_of_hamming_bits):
                del list_of_hamming_bits[position_of_next_redundant_bit]
            else:
                break

            number_of_iterations += 1

        return list_of_hamming_bits

    @staticmethod
    def ignore_remaining_bits(decoded_hamming_code: list) -> bool:

        bit_sum = 0

        for bit in decoded_hamming_code:
            bit_sum += bit

        if bit_sum == 0:
            return True

        return False

    @staticmethod
    def return_as_bits(data: bytes) -> list:

        data_as_bits = []

        for value in data:
            data_as_bits.extend([int(i) for i in str(np.binary_repr(value, 8))])

        return data_as_bits

    @staticmethod
    def add_lost_bits(data: list) -> list:

        while len(data) % 12 != 0:
            data.extend([0])

        return data
