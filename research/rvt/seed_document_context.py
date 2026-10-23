"""Typed remapping from measured seed base Level1916 to another requested level."""
from copy import deepcopy
from wall_element import GraphEncoder
from seed_wall_context import remap_graphs


def remap(graphs,declarations,mapping,*,new_id,base_level_id,base_elevation_feet,top_elevation_feet,type_width_feet):
    if type(base_level_id)is not int or base_level_id<=0 or base_level_id in (new_id,mapping[20307]):
        raise ValueError('requires distinct positive base, top and wall IDs')
    # The existing guard proves fixed seed context and geometric relocation.
    # Rebind only schema-typed Level1916 references after that operation.
    seed_mapping=dict(mapping);seed_mapping[20308]=1916
    actual_top=mapping[20307]
    temporary_top=2147483647 if actual_top==1916 else actual_top
    if temporary_top==new_id:raise ValueError('temporary reference collides with new wall')
    seed_mapping[20307]=temporary_top
    result,audit=remap_graphs(graphs,declarations,seed_mapping,new_id=new_id,
        base_elevation_feet=base_elevation_feet,top_elevation_feet=top_elevation_feet,type_width_feet=type_width_feet)
    if base_level_id==1916 and temporary_top==actual_top:return result,{**audit,'requested_base_level_id':base_level_id,'base_level_rebindings':[]}
    result=deepcopy(result);encoder=GraphEncoder(declarations);changes=[]
    def walk(tag,value,path):
        if encoder.classes[tag]['name']=='ElementId':
            old=value['m_id']['m_id64']
            if old==1916:
                value['m_id']['m_id64']=base_level_id;changes.append({'path':path,'before':old,'after':base_level_id})
            elif temporary_top!=actual_top and old==temporary_top:
                value['m_id']['m_id64']=actual_top;changes.append({'path':path,'before':old,'after':actual_top})
            return
        for name,_,field in encoder.layouts[tag]:
            if field['base']!=14 or (field['modifier']&15)in (1,2,3)or len(field['references'])!=1:continue
            child=field['references'][0]['tag']
            def descend(item,p):
                if isinstance(item,list):
                    for i,v in enumerate(item):descend(v,f'{p}[{i}]')
                elif isinstance(item,dict):walk(child,item,p)
            descend(value[name],path+'.'+name)
    for channel,graph in result.items():
        for index,obj in enumerate(graph['objects']):walk(obj['class_tag'],obj['fields'],f'{channel}.objects[{index}]')
    if not changes:raise ValueError('no measured base-level references found')
    root=result['102']['objects'][0]['fields']
    if root['m_assocLevelId']['m_id']['m_id64']!=base_level_id:raise ValueError('root base level was not rebound')
    if root['m_upToLevelId']['m_id']['m_id64']!=actual_top:raise ValueError('root top level was not rebound')
    return result,{**audit,'requested_base_level_id':base_level_id,'requested_top_level_id':actual_top,'base_level_rebindings':changes}
