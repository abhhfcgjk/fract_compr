import csv
import os
import argparse
import signal
import sys
import traceback
from contextlib import contextmanager
from skimage.transform import resize
from skimage import io
import numpy as np
from skimage.metrics import peak_signal_noise_ratio as psnr


QUALITY = 'quality'
COMPRESSED_SIZE = 'compressed_size'
PSNR = 'psnr'
CONCLUSION = 'conclusion'


class TestDirectoryNotFoundError(FileNotFoundError):
    pass


class TimeoutException(Exception): pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


quality = [0, 20, 40, 60, 80, 100]


def test_image(dir, name_img, timeout):
    img = np.rint(resize(io.imread(os.path.join(dir, name_img)), (256, 256)) * 255).astype('uint8')
    comp = FractalCompressor()
    results = []
    for q in quality:
        try:
            with time_limit(timeout):
                compressed_image = comp.compress2(img, quality=q)
                if not isinstance(compressed_image, bytearray):
                    results.append((q, None, None, f'FE: Compressed image is {type(compressed_image)} and not bytearray'))
                    continue
                decompressed_image = comp.decompress(compressed_image)
            if is_colored(img):
                results.append((q, len(compressed_image), weighted_psnr(img, decompressed_image), 'OK'))
            else:
                results.append((q, len(compressed_image), psnr(img, decompressed_image), 'OK'))
        except TimeoutException:
            results.append((q, None, None, 'TL'))
        except:
            results.append((q, None, None, f'RE: {traceback.format_exception(*sys.exc_info())}'))

    return results


def run_tests(test_dir, timeout=300):
    results = []
    
    for name in os.listdir(test_dir):
        results += test_image(test_dir, name, timeout)
        
    return tuple(results)


def save_results(results, filename='results.csv'):
    header = [QUALITY,
              COMPRESSED_SIZE,
              PSNR,
              CONCLUSION]
    with open(filename, 'w', newline='') as resfile:
        writer = csv.writer(resfile)
        writer.writerow(header)
        resfile.flush()
        for row in results:
            writer.writerow(row)
            resfile.flush()


def main():
    parser = argparse.ArgumentParser(description='Testing script')
    parser.add_argument('--timeout', type=float, default=300)
    parser.add_argument('--test_dir', type=str, default='test_files')
    parser.add_argument('--output_file', type=str, default='results.csv')

    args = parser.parse_args()

    try:
        results = run_tests(args.test_dir, args.timeout)
    except TestDirectoryNotFoundError as e:
        print('Failed to find test directory')
        print(e)
        return

    save_results(results, args.output_file)
    print('Results saved to: {}'.format(args.output_file))


if __name__ == '__main__':
    main()
