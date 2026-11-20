"""View-only vendor geometry in the same cropped pixel frame as calibration."""
def serialize(data, left=0, top=0):
    from vacuum_map_parser_base.map_data import Point
    dims=data.image.dimensions
    def point(p):
        q=p.to_img(dims).rotated(dims)
        return [q.x-left,q.y-top]
    paths=[]
    for name in ('path','mop_path'):
        value=getattr(data,name,None)
        for line in getattr(value,'path',[]) or []:
            if line: paths.append({'kind':name,'points':[point(p) for p in line]})
    obstacles=[point(p) for name in ('obstacles','obstacles_with_photo') for p in (getattr(data,name,None) or [])]
    restrictions=[]
    for name in ('no_go_areas','no_mopping_areas','no_carpet_areas','walls'):
        for a in getattr(data,name,None) or []:
            count=2 if name=='walls' else 4
            restrictions.append({'kind':name,'points':[point(Point(getattr(a,'x'+str(i)),getattr(a,'y'+str(i)))) for i in range(count)]})
    return {'path':paths,'obstacles':obstacles,'restrictions':restrictions,'carpetNote':'Carpet raster decoding unavailable; not inferred from map colours.'}
