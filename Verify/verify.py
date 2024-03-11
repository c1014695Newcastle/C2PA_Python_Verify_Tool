import c2pa, json

high_risk_actions = ['c2pa.cropped','c2pa.deleted','c2pa.placed','c2pa.removed']
medium_risk_actions = ['c2pa.color_adjustments','c2pa.drawing','c2pa.edited','c2pa.filtered','c2pa.redacted','c2pa.resized','c2pa.unknown',]


def check_errors(manifest_store):
    if 'validation_status' not in manifest_store.keys():
        return False
    return True

def check_metadata(manifest):
    score = 0
    for a in manifest:
        if a['label'] == 'stds.exif' or a['label'] == 'c2pa.metadata':
            for key in a['data'].keys():
                if any(word in key for word in ['Make', 'Model', 'Latitude', 'Longitude', 'TimeStamp']):
                    score += 1
    return score


def check_ai(manifest):
    for assertion in manifest:
        if assertion['label'] == 'c2pa.actions':
            for action in assertion['data']['actions']:
                if 'digitalSourceType' in action.keys() and 'trainedAlgorithmicMedia' in action['digitalSourceType']:
                    return True


def check_photoshop(manifest):
    risk = 0
    for assertion in manifest:
        if assertion['label'] == 'c2pa.actions':
            for action in assertion['data']['actions']:
                if action['action'] in high_risk_actions:
                    risk += 2
                elif action['action'] in medium_risk_actions:
                    risk += 1
    return risk


def verify(manifest_store):
    if check_errors(manifest_store):
        return -1
    active_manifest = manifest_store['manifests'][manifest_store['active_manifest']]['assertions']
    photoshop = check_photoshop(active_manifest)
    metadata_score = check_metadata(active_manifest)
    print('Photoshop: ', photoshop, '\nMetadata:', metadata_score)


verify(json.loads(
    c2pa.read_file('Images/truepic-20230212-library.jpg', None)))
