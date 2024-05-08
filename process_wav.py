import csv
import re
import argparse
from batdetect2 import api

FIELDS = [
    "filename",
    "timestamp",
    "duration",
    "Barbastellus barbastellus",
    "Eptesicus serotinus",
    "Myotis alcathoe",
    "Myotis bechsteinii",
    "Myotis brandtii",
    "Myotis daubentonii",
    "Myotis mystacinus",
    "Myotis nattereri",
    "Nyctalus leisleri",
    "Nyctalus noctula",
    "Pipistrellus nathusii",
    "Pipistrellus pipistrellus",
    "Pipistrellus pygmaeus",
    "Plecotus auritus",
    "Plecotus austriacus",
    "Rhinolophus ferrumequinum",
    "Rhinolophus hipposideros",
]


def create_timestamp(filename: str) -> str:
    """
    An ugly function that converts a wildlife acoustic wav filename to a timestamp
    """
    pattern = r"\d{8}_\d{6}"
    match = re.search(pattern, filename)
    if match:
        timestamp = match.group(0)
        formatted_timestamp = f"{timestamp[0:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
        return formatted_timestamp
    else:
        return None


# subclass of dict to create dict with default values of [0] for each species
class BatDict(dict):
    def __init__(self, *args, **kwargs):
        for field in FIELDS[3::]:
            self[field] = [0]


# command line arguments
parser = argparse.ArgumentParser()

parser.add_argument(
    "directory", help="Path to directory containing WAV files", default="."
)
parser.add_argument("output", help="Filename for output csv", default="output.csv")
parser.add_argument(
    "threshold",
    help="Detection threshold, a value from 0 to 1",
    default=0.5,
    type=float,
)

# assign args as variables
args = parser.parse_args()
wav_directory = args.directory
output_csv = args.output
threshold = args.threshold

# set config values
conf = api.get_config(
    detection_threshold=threshold,
    chunk_size=5,
    target_samp_rate=384000,
    min_freq_hz=16000,
)

# return list of audio files in wav directory
audio_files = api.list_audio_files(wav_directory)

# use context manager to create output file
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=FIELDS)

    audio_array_length = len(audio_files)

    writer.writeheader()

    for count, f in enumerate(audio_files, start=1):
        print(f"Processing file {count} of {audio_array_length}")
        # process files using custom config
        processed = api.process_file(f, config=conf)

        # for processed file, assign pred_dict as instance
        instance = processed["pred_dict"]

        # if instance has annotations
        if instance["annotation"]:
            species_data = BatDict()
            instance_dict = {}

            filename = instance["id"]

            instance_dict["filename"] = filename
            instance_dict["timestamp"] = create_timestamp(filename)
            instance_dict["duration"] = instance["duration"]

            for a in instance["annotation"]:
                species_data[a["class"]].append(a["class_prob"])

            for species, detections in species_data.items():
                instance_dict[species] = max(detections)

            writer.writerow(instance_dict)
    
    print("Processing complete")
    print("Script ending")
