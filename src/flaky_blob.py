
import os
marker_file = 'flaky_marker.tmp'
if not os.path.exists(marker_file):
    with open(marker_file, 'w') as f: f.write('failed')
    log('Flaky Blob: [FAILING] First attempt simulation')
    raise Exception('Transient Error')
else:
    os.remove(marker_file)
    log('Flaky Blob: [SUCCESS] Second attempt simulation')
    result = 'Success after retry!'

