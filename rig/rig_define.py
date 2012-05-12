import math, logging
import mathutils
import bpy

log = logging.getLogger ('rig-def')

def create_blender_armature (name, ctx):
  """create an empty armature data and object, put the armature
     into edit-mode and return the data object. The armature
     object will be the active object.
  """
  scene = ctx.scene
  armdat = bpy.data.armatures.new (name = name)
  armobj = bpy.data.objects.new (name = name, object_data = armdat)
  scene.objects.link (armobj)
  scene.objects.active = armobj
  armdat.show_axes = True
  return armobj

def transform_bone (orient, origin, bbone):
  """place and orient the blender bone bbone.
  """
  xyz_angles = [math.radians (angle) for angle in orient]
  orient_tf = mathutils.Euler (xyz_angles, 'XYZ').to_matrix ().to_4x4 ()
  bbone.transform (orient_tf)
  # somehow translating the bone with a combined matrix does not
  # work; the bone will always rotate a bit. So use the translate()-method.
  bbone.translate (mathutils.Vector (origin))

class bone_info (object):
  """store data on a created bone or bones.
     this is for the case when a single input bone would result in multiple
     blender bones to be created.
  """
  def __init__ (self, id = None):
    """create a new bone info object. id is the name of a single bone
       that leads to creation of this object.
    """
    self.id = id
    # bbones is the set of names of all blender bones that make
    # this bone.
    self.bbones = []
    # end gives the name of a blender bone that is used as a parent
    # whenever this bone is to have children.
    self.end = None
    # start is a set of names of blender bones that are to be used
    # whenever this bone needs to be connected to a parent.
    self.start = []

def insert_bone (si_bone, armdat):
  """insert the bone object into the armature data armdat and returns
     a bone_info object created for this bone.
     created bones are name 'def-<bodypart>.<axes>'
     si_bone must provide these attributes:
     orientation, origin - basic position data of the bone used to create
       the transformation of the bone in armature-space.
  """
  b_info = bone_info (id = si_bone.get ('id'))
  bbone_name = "def-%s.xyz" % (si_bone.get ('id'))
  b_bone = armdat.edit_bones.new (name = bbone_name)
  orient = si_bone.get ('orientation')
  origin = si_bone.get ('origin')
  # create an initial orientation by setting the tail of
  # the bone to 0,1,0. This leaves the bone pointing in the y-orientation,
  # so the local space is the same as the global space.
  b_bone.head = (0, 0, 0)
  b_bone.tail = (0, si_bone.get ('length'), 0)
  transform_bone (orient, origin, b_bone)
  b_info.bbones.append (bbone_name)
  b_info.start.append (bbone_name)
  b_info.end = bbone_name
  return b_info
  
def insert_bones (si_arm, armdat):
  """traverse the bones of the armature in preorder (parent before
     children) and insert them into the armature data.
     Returns a mapping of the names of the inserted bones to their definition.
  """
  bone_mapping = dict ()
  # the parent queue holds bone_info-objects whose children still 
  # need to get created.
  parent_queue = [None]
  while len (parent_queue) > 0:
    parent = parent_queue.pop ()
    log.info ("inserting children of %s", parent)
    if parent is not None:
      # the parent is a b-info object and the b-infos end-attribute contains
      # the blender-bone to which children need to get linked to.
      children = list (si_arm.get_children (parent.id))
      parent_bbone = armdat.edit_bones[parent.end]
    else:
      children = list (si_arm.get_children (None))
      parent_bbone = None
    for child in children:
      b_info = insert_bone (child, armdat)
      for bbone_start_name in b_info.start:
        bbone_start = armdat.edit_bones[bbone_start_name]
        bbone_start.parent = parent_bbone
      bone_mapping[b_info.id] = b_info
      parent_queue.append (b_info)
  return bone_mapping

# poser/daz bones are always based on euler rotations and might contain
# scale components. They might also contain translations, but those seem
# to be not fully complete bones, but are folded somehow into the
# standard bones (ie they have no weightmap).

def configure_bones (armdat, bone_mapping, armobj):
  """perform final fixups on the created bones.
  """
  pose_bones = armobj.pose.bones
  for (bone_name, b_info) in bone_mapping.items ():
    si_bone = armdat.get_bone (b_info.id)
    order = si_bone.get ('rotation_order')
    for bbone_name in b_info.bbones:
      bbone = pose_bones[bbone_name]
      bbone.rotation_mode = order

def define_armature (si_arm, ctx):
  """create a blender-armature object from the given armature-data.
     blender-function.
     ctx is the context for defining the armature in.
  """
  armobj = create_blender_armature ('imported-arm', ctx)
  bpy.ops.object.mode_set (mode = 'EDIT')
  bone_map = insert_bones (si_arm, armobj.data)
  bpy.ops.object.mode_set (mode = 'OBJECT')
  configure_bones (si_arm, bone_map, armobj)
  return armobj
