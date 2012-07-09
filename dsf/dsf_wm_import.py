import sys, os.path, logging, json
import bpy
import rig.weight_paint

from bpy.props import StringProperty, BoolProperty
from bpy_extras.io_utils import ImportHelper

import dsf.dsf_weightmap

log = logging.getLogger ("dsf-wm-imp")

def load_mod_lib (filepath):
  """load the dsf file and return the modifier-library.
  """
  ifh = open (filepath, 'r', encoding = 'latin1')
  jdata = json.load (ifh)
  ifh.close ()
  if 'node_library' in jdata:
    # return the first modifier library.
    return jdata['modifier_library'][0]
  else:
    raise KeyError ("data does not contain modifier-library.")
def load_skin (filepath):
  """load the dsf file and return a skin.
  """
  jdata = load_mod_lib (filepath)
  skin = dsf.dsf_weightmap.skin (jdata['skin'])
  return skin

# weight paint a mesh based on some loading options.
# options that should be possible:
# - merge all axes into one.
# - with or without scale
# when used with the armature import, it should also be possible to
# merge the two main axes into one, leaving the twist axis alone.

class import_dsf_wm (bpy.types.Operator):
  """operator to import a dsf armature.
  """
  bl_label = 'import dsf-wm'
  bl_idname = 'wm.dsf'

  filepath = StringProperty\
      ('file path', description = 'file path for dsf modifier-library.',\
         maxlen = 1000, default = '')
  merge = BoolProperty\
      (name = 'merge', description = 'merge the rotation axes into one.',
       default = True)
  scale = BoolProperty\
      (name = 'scale', description = 'import scaling weights.',
       default = False)
  filter_glob = StringProperty (default = '*.dsf')
  def define_wm (self, ctx, skin, **kwarg):
    """weight paint a mesh based on the loaded data in the skin-object.
       kwarg contains the import-options passed to the skin-object.
    """
    mshobj = ctx.scene.objects.active
    log.info ("define: %s", kwarg)
    paint_groups = skin.collect_all_paint_maps (**kwarg)
    for (group_name, paint_map) in paint_groups.items ():
      rig.weight_paint.paint_group (paint_map, mshobj, group_name)
  def execute (self, ctx):
    """load the modifier-library and put in onto the mesh.
    """
    log.info ("loading: %s", self.properties.filepath)
    skin = load_skin (self.properties.filepath)
    kwarg = {
      'merge': self.properties.merge,
      'scale': self.properties.scale
    }
    self.define_wm (ctx, skin, **kwarg)
    return {'FINISHED'}
  def invoke (self, ctx, event):
    """called by the menu entry or the operator menu.
    """
    ctx.window_manager.fileselect_add (self)
    return {'RUNNING_MODAL'}

def menu_func (self, ctx):
  """render the menu entry.
  """
  self.layout.operator (import_dsf_wm.bl_idname, text = 'dsf-weightmap (.dsf)')

def register ():
  """add the operator to blender.
  """
  bpy.utils.register_class (import_dsf_wm)
  bpy.types.INFO_MT_file_import.append (menu_func)

def unregister ():
  """remove the operator from blender.
  """
  bpy.utils.unregister_class (import_dsf_wm)
  bpy.types.INFO_MT_file_import.remove (menu_func)

genesis = '/images/winshare/dsdata4/data/DAZ 3D/Genesis/Base/Genesis.dsf'
