from collections import namedtuple

landcover_types = ['sea', 
                    'glacier',
                    'in_lake',
                    'ever_nl',
                    'ever_bl',
                    'deci_nl',
                    'deci_bl',
                    'trop_bl',
                    'dry_tr',
                    'ever_sh',
                    'deci_sh',
                    'thor_sh',
                    'shor_gr',
                    'long_gr',
                    'crops',
                    'rice',
                    'sugar',
                    'maize',
                    'cotton',
                    'irr_cr',
                    'urban',
                    'tundra',
                    'swamp',
                    'desert',
                    'mx_tree',
                    'mx_sh']

canopies = namedtuple('canopies', landcover_types, defaults=[0.0]*len(landcover_types))

# defaults from https://mesh-model.atlassian.net/wiki/spaces/USER/pages/6390712/Land+cover+types+in+SVS [2026-06-12]

z0v = namedtuple('z0v', landcover_types, 
                        defaults=[0.001,  # sea
                                  0.001,  # glacier
                                  0.001,  # in_lake
                                    1.75, # ever_nl
                                    2.0,  # ever_bl
                                    1.0,  # deci_nl
                                    2.0,  # deci_bl
                                    3.0,  # trop_bl
                                    0.8,  # dry_tr
                                    0.1,  # ever_sh
                                    0.2,  # deci_sh
                                    0.2,  # thor_sh
                                    0.1,  # shor_gr
                                    0.1,  # long_gr 
                                    0.15, # crops
                                    0.15, # rice
                                    0.35, # sugar
                                    0.25, # maize
                                    0.1,  # cotton
                                    0.25,  # irr_cr
                                    5.0, # urban
                                    0.1, # tundra
                                    0.1, # swamp
                                    0.1, # desert
                                    1.75, # mx_tree
                                    0.5]) # mx_sh

# also see https://cccma.gitlab.io/classic/basicInputs.html
z0v_classic = namedtuple('z0v_classic', landcover_types,
                    defaults=[0.001,  # sea
                            0.001,  # glacier
                            0.001,  # in_lake
                                1.5, # ever_nl
                                3.5,  # ever_bl
                                1.0,  # deci_nl
                                2.0,  # deci_bl
                                3.0,  # trop_bl
                                0.8,  # dry_tr
                                0.05,  # ever_sh
                                0.15,  # deci_sh
                                0.15,  # thor_sh
                                0.02,  # shor_gr
                                0.08,  # long_gr 
                                0.15, # crops
                                0.08, # rice
                                0.35, # sugar
                                0.25, # maize
                                0.1,  # cotton
                                0.08,  # irr_cr
                                1.35, # urban
                                0.01, # tundra
                                0.05, # swamp
                                0.1, # desert
                                1.75, # mx_tree
                                0.5]) # mx_sh