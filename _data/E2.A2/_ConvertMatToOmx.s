;script used to convert MTX or MAT files to OMX format
;no module needed because it runs in PILOT
;more info here: https://communities.bentley.com/products/mobility-simulation/w/cube-legion-wiki/59307/how-to-convert-omx-matrices-from-to-cube-matrices

convertmat from = "PA_AllPurp_GRAVITY.MTX"         to = "PA_AllPurp_GRAVITY.omx"         compression = 1 format = omx
convertmat from = "DISTMED_PA_Gravity_AllPurp.MTX" to = "DISTMED_PA_Gravity_AllPurp.omx" compression = 1 format = omx
convertmat from = "DISTLRG_PA_Gravity_AllPurp.MTX" to = "DISTLRG_PA_Gravity_AllPurp.omx" compression = 1 format = omx
