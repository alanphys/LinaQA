'''Verify the integrity of a set of python files
Author: Michael Altfield
Adpated from https://stackoverflow.com/questions/63568328/how-to-verify-integrity-of-files-using-digest-in-python-sha256sums
'''
from hashlib import sha256
import os


# Takes the path (as a string) to a SHA256SUMS file and a list of paths to
# local files. Returns true only if all files' checksums are present in the
# SHA256SUMS file and their checksums match
def integrity_is_ok(sha256sums_filepath, local_filepaths):

    # first we parse the SHA256SUMS file and convert it into a dictionary
    sha256sums = dict()
    with open(sha256sums_filepath) as fd:
        for line in fd:
            # sha256 hashes are exactly 64 characters long
            checksum = line[0:64]

            # there is one space followed by one metadata character between the
            # checksum and the filename in the `sha256sum` command output
            filename = os.path.split(line[66:])[1].strip()
            sha256sums[filename] = checksum

    # now loop through each file that we were asked to check and confirm its
    # checksum matches what was listed in the SHA256SUMS file
    for local_file in local_filepaths:

        local_filename = os.path.split(local_file)[1]

        sha256sum = sha256()
        with open(local_file, 'rb') as fd:
            data_chunk = fd.read(1024)
            while data_chunk:
                sha256sum.update(data_chunk)
                data_chunk = fd.read(1024)

        checksum = sha256sum.hexdigest()
        if checksum != sha256sums[local_filename]:
            return False

    return True
