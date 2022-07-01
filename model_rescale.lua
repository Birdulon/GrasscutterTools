local function find_active_char()
    local avatarroot = cs.UnityEngine.GameObject.Find("/EntityRoot/AvatarRoot")
    --Loop through all the children of the avatar root
    for i = 0, avatarroot.transform.childCount - 1 do
        local child = avatarroot.transform:GetChild(i)
        --If the child is active, return it
        if child.gameObject.activeInHierarchy then
            return child.gameObject
        end
    end
end


local function find_body(avatar)
    --unverified
    --Complete path looks something like
    --/EntityRoot/AvatarRoot/Avatar_Loli_Catalyst_Klee(Clone)/OffsetDummy/Avatar_Loli_Catalyst_Klee/Body
    local od = avatar.transform:Find("OffsetDummy")
    local av = od.transform:GetChild(0)
    return av.transform:Find("Body")
end


local function get_bone_container(bones, bc_name, bone_names)
    --Many bones are directly animated so we can't set their scale directly while animations are running
    --If we make a new transform and parent them to it, we can instead change the scale of that for them to inherit
    local bone_container = nil

    --See if the container with this name already exists
    for i = 0, bones.Length - 1 do
        local bone = bones[i]
        if bone.name == bc_name then  --We already made a container earlier
            return bone
        end
    end

    --We need to make a new container
    --Iterate over bones to find the ones we are looking for
    local target_bones = {}
    for i = 1, #bone_names do  --nil-initialize
        target_bones[i] = nil
    end
    for i = 0, bones.Length - 1 do
        local bone = bones[i]
        local bone_name = bone.name
        for j = 1, #bone_names do
            if bone_name == bone_names[j] then
                target_bones[j] = bone
            end
        end
    end

    for i = 1, #bone_names do
        if target_bones[j] == nil then
            cs.s.s("404 bone not found")
        return nil
    end

    --Should be /EntityRoot/AvatarRoot/<avatar>(Copy)/OffsetDummy/<avatar>/Bip001/Bip001 Pelvis/Bip001 Spine/Bip001 Spine1/Bip001 Spine2/
    local bone_parent = target_bones[bone_names[1]].transform.parent
    --Make new boobs container
    local bone_container = cs.UnityEngine.GameObject(bc_name)
    bone_container.transform.parent = bone_parent.transform
    bone_container.transform.localScale = cs.UnityEngine.Vector3(1, 1, 1)
    bone_container.transform.localEulerAngles = cs.UnityEngine.Vector3(0, 0, 0)
    bone_container.transform.localPosition = cs.UnityEngine.Vector3(0, 0, 0)
    --Reparent boob bones to this container
    for i = 1, #bone_names do
        target_bones[i].transform.parent = bone_container.transform
    end
    return bone_container
end

local function scale_bones(container_name, bone_names, scaling_mul)
    local avatar = find_active_char()
    --cs.s.s(avatar.name)
    
    if avatar then
        local body = find_body(avatar)
        local bones = body.transform:GetComponent(typeof(CS.UnityEngine.SkinnedMeshRenderer)).bones
        local bone_container = get_bone_container(bones, container_name, bone_names)

        if bone_container then
            bone_container.transform.localScale = cs.UnityEngine.Vector3(scaling_mul, scaling_mul, scaling_mul)
        end
    end
end

local function scale_breasts(scaling_mul)
    scale_bones("BreastContainer", {"+Breast L A01", "+Breast R A01"}, scaling_mul)
end


local function main()
    scale_breasts(3)
end

--Animation stuff
--/EntityRoot/AvatarRoot/Avatar_Loli_Catalyst_Klee(Clone)/OffsetDummy/Avatar_Loli_Catalyst_Klee
--Animator component -> UnityEngine.Animator
--Animator.runtimeAnimatorController -> UnityEngine.RuntimeAnimatorController
--RuntimeAnimatorController.animationClips -> array of UnityEngine.AnimationClip
