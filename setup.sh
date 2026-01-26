cd /projects/vig/yiwenc/ResearchProjects/lightingDiffusion/3dgs/render_objaverse
conda activate /projects/vig/yiwenc/all_env/blender-env

find -maxdepth 1 -type d | sort | while read -r dir; do n=$(find "$dir" -type f | wc -l); printf "%4d : %s\n" $n "$dir"; done
