# Log Analyser inside the logs folder and print which file has an error and warning

import os
for root, direc, files in os.walk("testlogs"):
    for name in files:
        path = os.path.join(root, name)
        error = warn = 0

        try:
            with open(path) as f:
                for line in f:
                    line = line.lower()
                    if "error" in line:
                        error += 1
                    elif "warn" in line:
                        warn += 1
        except OSError:
            continue

        if error > 0 or warn > 0:
            print(path, "-", error, "errors", warn, "warings")
