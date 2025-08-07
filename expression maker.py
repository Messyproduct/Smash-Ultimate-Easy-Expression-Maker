bl_info = {
    "name": "Smash Ultimate Easy Expression Maker",
    "category": "3D View",
    "author": "Messyproduct",
    "version": (0,1,0),
    "blender": (3,0,0),
    "location": "View3D > Sidebar > Ultimate Tab",
    "description": "A tool for creating expression meshes for Smash Ultimate",
}
import bpy
import re
import traceback

#Properties for Graphic User Interface
class MyProperties(bpy.types.PropertyGroup):
    
    basis_key : bpy.props.StringProperty(
        default="Basis"
    ) 
    eye_smooth_factor : bpy.props.FloatProperty(
        name= "Eye Smooth Factor:", 
        min=0, max=1,
        default=.3, 
        description="The rate at which eye expressions will smooth if Smooth Border is activated"
    )
    eye_smooth_steps : bpy.props.IntProperty(
        name= "Eye Smooth Steps:", 
        default=3, 
        min=0, soft_max=10,
        description="How many vertices the smoothing will occur over for eye expressions"
    )    
    mouth_smooth_factor : bpy.props.FloatProperty(
        name= "Mouth Smooth Factor:", 
        min=0,max=1,default=.3, 
        description="The rate at which mouth expressions will smooth if Smooth Border is activated"
    )
    mouth_smooth_steps : bpy.props.IntProperty(
        name= "Mouth Smooth Steps:", 
        default=3,min=0, soft_max=10,
        description="How many vertices the smoothing will occur over for mouth expressions"
    )
    do_batch : bpy.props.BoolProperty(
        name= "Batch Convert All", 
        default=False,
        description="If checked a mesh will be created for each key, if not only the active shape key"
    ) 
    do_verbose : bpy.props.BoolProperty(
        name= "Verbose Logging", 
        default=False,
        description="If checked python log will be more detailed, for debugging"
    ) 
    do_baseface : bpy.props.BoolProperty(
        name= "Make Base Face", 
        default=False,
        description="Create base face mesh?"
    )
    smooth_enum : bpy.props.EnumProperty(
        name= "",
        description= "Choose the desired smoothing option",
        items= [('1', "Smooth Border", "Smooth the bordering vertices to better hide seams"),
                ('2', "Connect Edges Only", "Connect outer boundary vertices to base only"),
                ('0', "Do Nothing", "Leave outer boundary vertices untouched; edges may be disconnected")
        ]
    )
    clean_enum : bpy.props.EnumProperty(
        name= "",
        description= "Choose the desired cleanup option",
        items= [('1', "Full Clean", "Remove all shape keys after mesh creation"),
                ('2', "Partial Clean", "Remove shape keys that aren't basis and target"),
                ('0', "No Clean", "Do not delete any shape keys")
        ]
    )

#Class for user interface drawing
class UserGUI(bpy.types.Panel):
    bl_label = "Easy Expression Maker"
    bl_idname = "VIEW3D_PT_EasyExpressionMaker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Ultimate'
    
    def draw(self, context):
        object = context.object
        layout = self.layout
        scene = context.scene
        props = scene.props
        
        box = layout.box()
        row = box.row()
        try:
            row.label(text="Active object is: " + object.name)
        except:
            row.label(text="Active object is: ")
        row = box.row()
        row.label(text="Split Target:")
        row.prop(context.scene, "target_object")

        
        try:
            bpy.context.scene.target_object.name
        except:
            return
        else:
            layout.separator()
            box = layout.box()
            row = box.row(align=True)
            row.label(text="Eye Vertex Group:")
            eye_vertex_group=row.prop_search(context.scene, "eyever", scene.target_object, "vertex_groups", text="")
            
            row = box.row(align=True)
            row.label(text="Mouth Vertex Group:")
            mouth_vertex_group=row.prop_search(context.scene, "mouthver", scene.target_object, "vertex_groups", text="")
            
            
            row = box.row(align=True)
            row.label(text="Base Vertex Group:")
            base_vertex_group=row.prop_search(context.scene, "basever", scene.target_object, "vertex_groups", text="")
            
            layout.separator()
            box = layout.box()
            
            
            row = box.row()
            try:
                row.label(text="Active Shapekey is: " + scene.target_object.active_shape_key.name)
            except:
                row.label(text="Mesh has no Shapekeys")
                return
            
            row = box.row(align=True)
            row.label(text="Basis Shape Key:")
            row.prop(props,"basis_key", text="",icon='SHAPEKEY_DATA')
        
            
            
            row = box.row(align=True)
            row.label(text="Smooth Mode:")
            row.prop(props,"smooth_enum")
            
            row = layout.row(align=True)
            
            row.prop(props,"eye_smooth_factor")
            row.prop(props,"eye_smooth_steps")
            row = layout.row(align=True)
            
            row.prop(props,"mouth_smooth_factor")
            row.prop(props,"mouth_smooth_steps")
            
            layout.separator()
            box = layout.box()
            layout.separator()
            
            row = box.row(align=True)
            
            row.label(text="Clean-up Mode:")
            row.prop(props,"clean_enum")
            
            row = layout.row(align=True)
            
            row.prop(props,"do_batch")
            row.prop(props,"do_baseface")
            row.prop(props,"do_verbose")
            
            layout.separator()

            
            row = layout.row(align=True)
            row.operator("sub.expressioninit")

#Class creates operator to handle exceptions and initialize the expressionmaker class
class Init(bpy.types.Operator):
    bl_label = "Make Me Some Expressions!"
    bl_idname = "sub.expressioninit"
    def execute(self, context):
        eyegroup=bpy.data.scenes["Scene"].eyever
        mouthgroup=bpy.data.scenes["Scene"].mouthver
        basegroup=bpy.data.scenes["Scene"].basever
        
        if(len(bpy.context.selected_objects)!=1):
            self.report({'ERROR'}, "Select the Split target object and only the split target object")
            return {"FINISHED"}
        
        if(eyegroup == "" or mouthgroup == "" or basegroup == ""):
            self.report({'ERROR'}, "Not all required data has been entered")
            return {"FINISHED"}
        
        if(bpy.context.object.name!=bpy.data.scenes["Scene"].target_object.name):
            self.report({'ERROR'}, "Split Target must be active object!")
            return {"FINISHED"}
            
        if(re.search("(.[0-9][0-9][0-9])", context.object.name)!=None):
            self.report({'ERROR'}, "Split target name must be unique from other objects! no .001 .002 .003...")
            return {"FINISHED"}
            
        itemreg="(.[0-9][0-9][0-9])"
        count=0
        
        for item in bpy.context.scene.objects:
            if(re.sub(itemreg, '', item.name)==context.object.name):
                count=count+1
                if(count==2):
                    self.report({'ERROR'}, "There is another object with the same name as split target: "+context.object.name)
                    return {"FINISHED"}
        
        shapefind=False
        for shapekey in bpy.context.active_object.data.shape_keys.key_blocks:        
            if(shapekey.name==bpy.data.scenes["Scene"].props.basis_key):
                shapefind=True
        
        if(shapefind==False):
            self.report({'ERROR'}, "Basis Shape key: "+bpy.data.scenes["Scene"].props.basis_key+", does not exist")
            return {"FINISHED"}
            
        run = ExpressionMaker(
            eyegroup, 
            mouthgroup, 
            basegroup, 
            bpy.data.scenes["Scene"].props.basis_key, 
            int(bpy.data.scenes["Scene"].props.smooth_enum), 
            int(bpy.data.scenes["Scene"].props.clean_enum), 
            bpy.data.scenes["Scene"].props.eye_smooth_factor, 
            bpy.data.scenes["Scene"].props.eye_smooth_steps, 
            bpy.data.scenes["Scene"].props.mouth_smooth_factor, 
            bpy.data.scenes["Scene"].props.mouth_smooth_steps, 
            bpy.data.scenes["Scene"].props.do_batch, 
            bpy.data.scenes["Scene"].props.do_verbose, 
            bpy.data.scenes["Scene"].props.do_baseface
        )
        
        try:
            run.main()
        except:
            self.report({'ERROR'}, "Something went wrong, it may be a bug or user error. Please inform Messyproduct via a github issue including the error message:\n"+traceback.format_exc())
            return {"FINISHED"}

        return {"FINISHED"}

#Class is passed all values as an object, generates expression meshes based on user selections
class ExpressionMaker():
    eye_group = 'Expressions Eyes'          #Vertex Group for eye meshes
    mouth_group = 'Expressions Mouth'       #Vertex Group for mouth meshes
    boundary_group = 'Expressions Base'     #the rest of the face mesh, e.g. what remains of the original mesh after the faces in the 2 above groups are erased

    basis_shape = 'face_neutral'

    smooth_mode=1                           #Use smoothing factors below to make the expression more seamless           1:Messy's Smooth,   2:Only connect touching faces                  0:Leave Faces unconnected
    cleanup_mode=1                          #Delete Shape Keys after process is complete?                               1:Delete all,       2:Delete everything but Basis and target,      0:Delete Nothing

    eye_smooth_factor=.30                   #Accepted Values: 0.00-1.00, The rate at which eye expressions will smooth if smooth_mode is activated
    eye_smooth_steps=3                      #Accepts any positive integer, How many vertices the eye smoothing will occur over if smooth_mode is activated, e.g. 1 = no smoothing, 4 = smooth 4 loop cuts deep

    mouth_smooth_factor=.30                 #Accepted Values: 0.00-1.00 The rate at which mouth expressions will smooth if smooth_mode is activated
    mouth_smooth_steps=3                    #Accepts any positive integer, How many vertices the mouth smoothing will occur over if smooth_mode is activated, e.g. 1 = no smoothing, 4 = smooth 4 loop cuts deep
        
        
    do_batch=True                           #Create an expression mesh for every shape key?                             True:Yes or False:No, only the currently selected one
    do_verbose=True
    do_baseface=True

    #list of common eye expression terms for use in type_decider function
    eye_dict=['eye', 'blink', 'harf', 'half']
    
    #list of other common expression terms for use in type_decider function; runs after eye meshes are decided so term overlap is okay
    mouth_dict=['mouth','face','ouch','down','talk','heavyattack','voice','pattern','escape','attack''heavyouch','ottotto','fura','hot','bound','result']
    
    #constructor to create new expression maker object
    def __init__(self, eye_group, mouth_group, boundary_group, basis_shape, smooth_mode, cleanup_mode, eye_smooth_factor, eye_smooth_steps, mouth_smooth_factor, mouth_smooth_steps, do_batch, do_verbose, do_baseface):  
        self.eye_group = eye_group  
        self.mouth_group = mouth_group
        self.boundary_group = boundary_group
        self.basis_shape = basis_shape
        self.smooth_mode = smooth_mode
        self.cleanup_mode = cleanup_mode
        self.eye_smooth_factor = eye_smooth_factor
        self.eye_smooth_steps = eye_smooth_steps
        self.mouth_smooth_factor = mouth_smooth_factor
        self.mouth_smooth_steps = mouth_smooth_steps
        self.do_batch = do_batch
        self.do_verbose = do_verbose
        self.do_baseface = do_baseface
    
    #main function to call subfunctions in correct order
    def main(self):
        self.v_print("================================================\nStarting Execution\n================================================")
        #print(self.eye_smooth_factor)
        #print(self.eye_smooth_steps)
        #print(self.mouth_smooth_factor)
        #print(self.mouth_smooth_steps)
        
        #print(self.do_batch)
        #print(self.do_baseface)
        #print(self.do_verbose)
        
        main_mesh=bpy.context.active_object
        main_shape=bpy.context.object.active_shape_key_index
        if(self.do_baseface==True):
                bpy.context.object.active_shape_key_index = 0
                self.duplicate(bpy.context.object)
                bpy.context.object.name='base_face'
                self.base()
                self.remove_all_shapekeys(0)
                
                bpy.ops.object.select_all(action='DESELECT')
                bpy.data.objects[main_mesh.name].select_set(True)
                bpy.context.view_layer.objects.active = main_mesh
                bpy.context.object.active_shape_key_index = main_shape
                
        if(self.do_batch==True):self.iterator(main_mesh)
        else:
            self.v_print("MAIN: Iterator Off")
            self.single(main_mesh)

        self.v_print("================================================\nEnding Execution\n================================================")
    
    #Duplicates Selected Mesh as to not tamper with original   
    def duplicate(self, mesh_name):   
        self.v_print("DUPLICATING: Mesh name to duplicate: "+mesh_name.name)
        self.change_mode('OBJECT')
        bpy.ops.object.duplicate(linked=False)
        bpy.data.objects[mesh_name.name+".001"].select_set(True)
        bpy.context.object.name=bpy.context.object.active_shape_key.name
        return
    
    #Runs Splitting process on a single mesh
    def single(self, s_selected):
        self.v_print("SINGLE EXPRESSION SPLIT: Single Selected Mesh: "+s_selected.name)
        bpy.context.view_layer.objects.active=s_selected
        
        key_type=self.type_decider(bpy.context.object.active_shape_key.name)
        if(key_type!=1):
            self.duplicate(bpy.context.object)
        
        if key_type=='mouth':
            if self.smooth_mode==1:
                self.smooth(self.mouth_smooth_factor, self.mouth_smooth_steps)
            elif self.smooth_mode==2:
                self.smooth(1,1)
            else:
                self.v_print("SINGLE EXPRESSION SPLIT: No smoothing will be done")  
                
            if self.cleanup_mode==1:
                self.remove_all_shapekeys(bpy.context.object.active_shape_key_index)
            elif self.cleanup_mode==2:
                self.remove_other_shapekeys(bpy.context.object.active_shape_key_index)
            else:
                self.v_print("SINGLE EXPRESSION SPLIT: No cleanup selected")

            self.mouth()
                
        elif key_type=='eyes':
            
            if self.smooth_mode==1:
                self.smooth(self.eye_smooth_factor, self.eye_smooth_steps)
            elif self.smooth_mode==2:
                self.smooth(1,1)
            else:
                self.v_print("SINGLE EXPRESSION SPLIT: No smoothing will be done")   
            
            if self.cleanup_mode==1:
                self.remove_all_shapekeys(bpy.context.object.active_shape_key_index)
            elif self.cleanup_mode==2:
                self.remove_other_shapekeys(bpy.context.object.active_shape_key_index)
            else:
                self.v_print("SINGLE EXPRESSION SPLIT: No cleanup selected")

            self.eyes()
                
        else:
            self.v_print("SINGLE EXPRESSION SPLIT: Shape key name did not match any known expression keyword")
        
        

        self.change_mode('OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[s_selected.name].select_set(True)
        bpy.context.view_layer.objects.active = s_selected
        self.v_print("SINGLE EXPRESSION SPLIT: Single Selected Mesh: "+s_selected.name)
    
    #Iterates through all shape keys on active mesh and sends to single generator function
    def iterator(self, i_selected):
            self.v_print("ITERATOR QUEUE: Iterator On")
            i = 0
            for shapekey in bpy.context.active_object.data.shape_keys.key_blocks:
                bpy.context.object.active_shape_key_index = i
                self.v_print("ITERATOR QUEUE: Iteration: "+str(bpy.context.object.active_shape_key_index))
                i=i+1

                self.v_print("ITERATOR QUEUE: iterator selected mesh: "+i_selected.name)
                self.v_print("ITERATOR QUEUE: iterator selected Shapekey: "+str(bpy.context.object.active_shape_key_index))

                self.single(i_selected)
    
    #Determines what type of mesh the shape key will be split into based on predefined list
    def type_decider(self, shape_name):
        for item in self.eye_dict:
            if item in shape_name.lower():
                self.v_print("TYPE DECIDER: Shape key "+shape_name+" contained the word "+item+" found in the eye dictionary")
                return 'eyes'
            else:
                continue   
        
        for item in self.mouth_dict:
            if item in shape_name.lower():
                self.v_print("TYPE DECIDER: Shape key "+shape_name+" contained the word "+item+" found in the mouth dictionary")
                return 'mouth'

                    
        self.v_print("TYPE DECIDER: Shape key "+shape_name+" did not contain any known dictionary item, skipping")        
        return 1
    
    #Splits mesh into a mouth expression
    def mouth(self):    
        self.v_print("MOUTH SPLIT: Generating new mouth mesh")
        self.change_mode('EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group=self.mouth_group)
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='FACE')
    
    #Splits mesh into an eye expression
    def eyes(self):
        self.v_print("EYE SPLIT: Generating new Eye mesh")
        self.change_mode('EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group=self.eye_group)
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='FACE')
    
    #Splits mesh into a baseface mesh
    def base(self):
        self.v_print("BASE SPLIT: Generating new Base Face mesh")
        self.change_mode('EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group=self.boundary_group)
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.delete(type='FACE')
    
    #accepts 2 parameters to control smoothing expressions into the base face
    def smooth(self, smooth_factor, smooth_steps):    
        self.change_mode('EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        current_blend=1.0
        
        if(bpy.context.object.active_shape_key_index==0):
            self.v_print("SMOOTHING: Shape key is the basis shape, no need for smoothing")
            return 
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        bpy.ops.object.vertex_group_set_active(group=self.boundary_group)
        bpy.ops.object.vertex_group_select()
        
        for i in range(smooth_steps):
            self.v_print("SMOOTHING: Iteration: "+str((1+i))+" Current Blend Value: "+str(round(current_blend, 2)))
            bpy.ops.mesh.blend_from_shape(shape=self.basis_shape, blend=current_blend, add=False)
            current_blend=current_blend-smooth_factor
            bpy.ops.mesh.select_more()
    
    #Cleans up the remaining shape keys and morphs the geometry to the currently selected shape key
    def remove_all_shapekeys(self, position):    
        self.change_mode('OBJECT')
        if(bpy.context.object.active_shape_key_index==0):
            bpy.ops.object.shape_key_remove(all=True)
            return
        if(bpy.context.object.active_shape_key_index==1):
            bpy.context.object.active_shape_key_index = 0
            bpy.ops.object.shape_key_remove(all=False)
            bpy.ops.object.shape_key_remove(all=True)
            return
        bpy.context.object.active_shape_key_index = position
        bpy.ops.object.shape_key_move(type='TOP')
        bpy.context.object.active_shape_key_index = 0
        bpy.ops.object.shape_key_remove(all=False)
        bpy.ops.object.shape_key_remove(all=True)
    
    #Removes all shape keys except the active one and the basis, for use with manually smoothing
    def remove_other_shapekeys(self, position):
        i=0
        self.change_mode('OBJECT')
        name1=bpy.context.active_object.data.shape_keys.key_blocks[0].name
        name2=bpy.context.active_object.data.shape_keys.key_blocks[position].name

        for shapekey in bpy.context.active_object.data.shape_keys.key_blocks:
            self.v_print("CLEANING: Checking current Shape Key Name: "+shapekey.name)
            if(shapekey.name==name1 or shapekey.name==name2):
                self.v_print("CLEANING: Protected Shape key found moving on to others")   
                i=i+1
            else:
                bpy.context.object.active_shape_key_index = i
                self.v_print("CLEANING: Deleting current Shape Key Index: "+str(bpy.context.object.active_shape_key_index))
                bpy.ops.object.shape_key_remove(all=False)
    
    #function that only prints if the verbose option is chosen
    def v_print(self, item):
        if(self.do_verbose==True):
            print(item)
        return
    
    #helper function to aid in code readability, forces switch to proper mode to avoid context errors
    def change_mode(self, mode_type):     
        bpy.ops.object.mode_set(mode=mode_type, toggle=False)


#Registration Functions       
def register():
    bpy.utils.register_class(MyProperties)
    bpy.utils.register_class(UserGUI)
    bpy.utils.register_class(Init)
    
    bpy.types.Scene.eyever = bpy.props.StringProperty(name="vertex_group_eye")
    bpy.types.Scene.mouthver = bpy.props.StringProperty(name="vertex_group_mouth")
    bpy.types.Scene.basever = bpy.props.StringProperty(name="vertex_group_base")
    
    bpy.types.Scene.target_object = bpy.props.PointerProperty(
        type = bpy.types.Object,
        name = "",
        description = "Mesh that contains all the expression shape keys that you would like to split"
    )
    
    bpy.types.Scene.props = bpy.props.PointerProperty(type=MyProperties) 
def unregister():
    bpy.utils.unregister_class(MyProperties)
    bpy.utils.unregister_class(UserGUI)
    bpy.utils.unregister_class(Init)
    
    del bpy.types.Scene.eyever
    del bpy.types.Scene.mouthver
    del bpy.types.Scene.basever
    del bpy.types.Scene.target_object
    del bpy.types.Scene.props
if __name__ == "__main__":
    register()