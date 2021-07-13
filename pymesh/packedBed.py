"""
PackedBed class

contract:
    - @input: read config
    - read packing file
    - modify packing (scale, shift, scale-particle-radii)
    - generate geos for particles

"""

from pymesh.tools import bin_to_arr, grouper, deep_get
from pymesh.bead import Bead

import numpy as np
import gmsh

class PackedBed:

    config = {}

    def __init__(self, config):
        self.config = config

        self.fname = deep_get(self.config, 'packing.file.name')
        self.dataformat = deep_get(self.config, 'packing.file.dataformat')
        self.zBot = deep_get(self.config, 'packing.zbot')
        self.zTop = deep_get(self.config, 'packing.ztop')
        self.nBeads = deep_get(self.config, 'packing.nbeads', 0)
        self.scaling_factor = deep_get(self.config, 'packing.scaling_factor')
        self.particles_scaling_factor = deep_get(self.config, 'packing.particles.scaling_factor')

        self.read_packing()
        if deep_get(self.config, 'packing.auto_translate'):
            self.moveBedtoCenter()
        self.generate()
        self.set_mesh_fields()

    def read_packing(self):
        # dataformat = "<f" ## For old packings with little endian floating point data. Use <d for new ones
        self.beads = []
        arr = bin_to_arr(self.fname, self.dataformat)
        if self.nBeads < 0:
            for chunk in grouper(arr,4):
                if (chunk[2] >= self.zBot/self.scaling_factor) and (chunk[2] <= self.zTop/self.scaling_factor):
                    x = chunk[0] * self.scaling_factor
                    y = chunk[1] * self.scaling_factor
                    z = chunk[2] * self.scaling_factor
                    r = chunk[3]/2 * self.scaling_factor * self.particles_scaling_factor
                    self.beads.append(Bead(x, y, z, r))
        else:
            for index, chunk in enumerate(grouper(arr,4)):
                if index == self.nBeads:
                    break
                x = chunk[0] * self.scaling_factor
                y = chunk[1] * self.scaling_factor
                z = chunk[2] * self.scaling_factor
                r = chunk[3]/2 * self.scaling_factor * self.particles_scaling_factor
                self.beads.append(Bead(x, y, z, r))


    def asDimTags(self):
        return [ (3,tag) for tag in self.entities ]

    def asCopyDimTags(self):
        return gmsh.model.occ.copy([ (3,tag) for tag in self.entities ])

    def asTags(self):
        return self.entities

    def updateBounds(self):
        """
        Calculate bounding points for the packed bed.
        """

        xpr = []
        xmr = []
        ypr = []
        ymr = []
        zpr = []
        zmr = []
        z = []

        for bead in self.beads:
            xpr.append(bead.x + bead.r)
            xmr.append(bead.x - bead.r)
            ypr.append(bead.y + bead.r)
            ymr.append(bead.y - bead.r)
            zpr.append(bead.z + bead.r)
            zmr.append(bead.z - bead.r)
            z.append(bead.z)

        radList = [ bead.r for bead in self.beads ]
        self.rmax = max(radList)
        self.rmin = min(radList)
        self.ravg = sum(radList)/len(radList)

        self.xmax = max(xpr)
        self.ymax = max(ypr)
        self.ymin = min(ymr)
        self.xmin = min(xmr)
        self.zmax = max(zpr)
        self.zmin = min(zmr)

        self.R = max((self.xmax-self.xmin)/2, (self.ymax-self.ymin)/2) ## Similar to Genmesh
        self.h = self.zmax - self.zmin
        self.CylinderVolume = np.pi * self.R**2 * self.h

    def moveBedtoCenter(self):
        """
        Translate bed center to origin of coordinate system.
        """
        self.updateBounds()
        offsetx = -(self.xmax + self.xmin)/2
        offsety = -(self.ymax + self.ymin)/2
        for bead in self.beads:
            bead.x = bead.x + offsetx
            bead.y = bead.y + offsety
        self.updateBounds()

    def generate(self):
        """
        Create packed bed entities
        """
        factory = gmsh.model.occ
        self.entities = []
        for bead in self.beads:
            self.entities.append(factory.addSphere(bead.x, bead.y, bead.z, bead.r))

    def set_mesh_fields(self):
        factory = gmsh.model.occ
        field = gmsh.model.mesh.field

        meshsize = deep_get(self.config, 'mesh.size', 0.2)
        meshsizeout = deep_get(self.config, 'mesh.sizeout', meshsize)
        meshsizein = deep_get(self.config, 'mesh.sizein', meshsize)

        self.center_points = []
        for bead in self.beads:
            ctag = factory.addPoint(bead.x, bead.y, bead.z, meshsizein)
            self.center_points.append(ctag)

            self.dtag = field.add('Distance')
            field.setNumbers(self.dtag, 'PointsList', [self.dtag])

            distmin = deep_get(self.config, 'mesh.field.threshold.rad_min_factor', 1) * bead.r
            distmax = deep_get(self.config, 'mesh.field.threshold.rad_max_factor', 1) * bead.r

            self.ttag = field.add('Threshold')
            field.setNumber(self.ttag, "InField", self.dtag);
            field.setNumber(self.ttag, "SizeMin", meshsizein);
            field.setNumber(self.ttag, "SizeMax", meshsizeout);
            field.setNumber(self.ttag, "DistMin", distmin);
            field.setNumber(self.ttag, "DistMax", distmax);
