"""Local room metadata: never renames cloud rooms or changes robot settings."""
def key(floor,room): return str(floor)+":"+str(room)
def validate(value,maps):
    if not isinstance(value,dict): raise ValueError("Expected room preferences")
    floor,room=value.get("floor"),value.get("room")
    if type(floor) is not int or type(room) is not int: raise ValueError("Invalid floor/room")
    target=next((m for m in maps if m["id"]==floor),None)
    if target is None or room not in [r["id"] for r in target.get("rooms",[])]: raise ValueError("Unknown floor/room")
    result={"floor":floor,"room":room}
    for field,limit in [("alias",80),("notes",1000)]:
        text=value.get(field,"")
        if not isinstance(text,str) or len(text)>limit: raise ValueError("Invalid "+field)
        result[field]=text.strip()
    if value.get("mode") not in ("vacuum","vacuum_and_mop","mop"): raise ValueError("Invalid default mode")
    result["mode"]=value["mode"]
    return result
