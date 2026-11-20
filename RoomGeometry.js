// Exact captured cells only. Source-image coordinates; no nearest-room guess.
function roomAt(mask, rooms, x, y) {
    if (!mask || mask.coordinateFrame !== "cropped-image-pixels" ||
        !Array.isArray(mask.rooms) || !Array.isArray(rooms) ||
        !Number.isFinite(x) || !Number.isFinite(y)) return null;
    var found = null;
    for (var row of mask.rooms) {
        if (!Number.isInteger(row.id) || !rooms.some(function(r){return r.id === row.id}) || !Array.isArray(row.rects)) continue;
        for (var rect of row.rects) {
            if (!Array.isArray(rect) || rect.length !== 4 || !rect.every(Number.isFinite) || rect[2] <= 0 || rect[3] <= 0) continue;
            if (x >= rect[0] && x < rect[0]+rect[2] && y >= rect[1] && y < rect[1]+rect[3]) {
                if (found !== null && found !== row.id) return null;
                found = row.id;
            }
        }
    }
    return found;
}
