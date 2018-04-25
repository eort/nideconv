"""
# make masks
I thought of one thing you could try, 
to not just cut up a big ROI at arbitrary locations. 
So, for example, take your big PFC ROI. I would:

1) load the frontal pole mask the Harvard-Oxford Cortical Structural atlas in fsleyes
2) Change the threshold to a very strict probability, say minimum threshold of 70 (70% probability)
3) Save this as a binary mask (#1) (either each hemisphere separately or together, your choice)
4) change the probability to something less conservative, like 50
5) Save this as a binary mask (#2)
6) Repeat as necessary

In the end, you will have a series of masks covering larger and 
larger area. You can use these masks as location cutoffs to split 
up your big PFC mask. So, for example, to only get the PFC area 
covered by mask 1, combine your binarized PFC mask with the binarized 
mask #1 using this syntax:

fslmaths roi1 -add roi2 -outputfile

Any overlap between them will have a value of 2, 
any independent coverage from each mask will have a value of 1, 
and the rest of the brain’s voxels will have a value of 0. 
You can view this new combined mask in fsleyes. 
Now, set your minimum value to 2, 
and the combined mask will show you only the voxels that have 
overlap between the two masks. You can save this thresholded image as 
a new mask (e.g., "PFC_FParea1") 
and voila- your PFC mask restricted to a smaller area.

To get the next area of coverage, combine mask 2. as before
But now you have one more step- subtract “PFC_FParea1” from “big_mask” 
using fslmaths so that you have a mask covering unique area:

fslmaths roi2 –sub roi1 –outputfile

Save the new mask as “PFC_FParea2” or whatever.

You can use this method to go further and further away from frontal pole, for example.



fslmaths is magic for creating ROIs to almost any 
specification you want. 
You can define spheres of any size with the center at any 
MNI coordinate. 
If you would rather do the univariate contrast-based ROI and 
yours is currently too big, 
I would suggest opening your nifti image with the t/z stat of interest 
and shrink down your activated area with the 
thresholding feature in fsleyes (raise the minimum z stat to 
5 instead of 3, for example) and then save that as a binary mask. 
If you would rather actually chop up the big ROI 
into different parts, you can use fslmaths to "zero out" 
sections of the brain. 
Let me know which of these you want to do and 
I will brush up on exactly how to do it with the command line 
functions and get back to you tomorrow.
"""



fslmaths /usr/share/fsl/5.0/data/standard/MNI152_T1_1mm_brain_mask   -roi -8 10 11 10 47 10 0 1  pointMask
fslmaths pointMask.nii.gz -kernel sphere 10 -fmean sphere_mask
fslmaths sphere_mask -bin sphere_mask