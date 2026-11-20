"""Fail-closed validation against freshly fetched device routines."""
def validate(request, available):
    if not isinstance(request, dict) or request.get('reviewed') is not True:
        raise ValueError('Confirm routine steps and physical floor in the official app first')
    identifier=request.get('id')
    if type(identifier) is not int or identifier not in [r.id for r in available]:
        raise ValueError('Routine no longer available for this device')
    return identifier
