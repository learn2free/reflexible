"""
Definition of the different data structures in reflexible.
"""

import datetime
import itertools

import numpy as np
import netCDF4 as nc


class Header(object):
    """This is the primary starting point for processing FLEXPART output.

    It contains all the metadata from the simulation run and tries to
    fake the behaviour of the `Header` of former ``pflexible`` package
    (that still lives in the ``reflexible.conv2netcdf4`` subpackage).

    This version is using a netCDF4 file instead of a native FLEXPART
    format.

    Usage::

        > H = Header(inputpath)
        > H.keys()   # provides a list of available attributes

    Parameters
    -----------
      path : string
        The path of the netCDF4 file.

    """

    @property
    def alt_unit(self):
        # XXX this depends on H.kindz, which is not in netCDF4 file (I think)
        return 'unkn.'

    @property
    def outlon0(self):
        return self.nc.outlon0

    @property
    def outlat0(self):
        return self.nc.outlat0

    @property
    def dxout(self):
        return self.nc.dxout

    @property
    def dyout(self):
        return self.nc.dyout

    @property
    def ibdate(self):
        return self.nc.ibdate

    @property
    def ibtime(self):
        return self.nc.ibtime

    @property
    def iedate(self):
        return self.nc.iedate

    @property
    def ietime(self):
        return self.nc.ietime

    @property
    def loutstep(self):
        return self.nc.loutstep

    @property
    def loutaver(self):
        return self.nc.loutaver

    @property
    def loutsample(self):
        return self.nc.loutsample

    @property
    def lsubgrid(self):
        return self.nc.lsubgrid

    @property
    def lconvection(self):
        return self.nc.lconvection

    @property
    def ind_source(self):
        return self.nc.ind_source

    @property
    def ind_receptor(self):
        return self.nc.ind_receptor

    @property
    def ldirect(self):
        return self.nc.ldirect

    @property
    def iout(self):
        return self.nc.iout

    @property
    def direction(self):
        if self.nc.ldirect < 0:
            return "backward"
        else:
            return "forward"

    @property
    def nspec(self):
        return len(self.nc.dimensions['numspec'])

    @property
    def species(self):
        l = []
        for i in range(self.nspec):
            if self.iout in (1, 3, 5):
                varname = "spec%03d_mr" % (i + 1)
            if self.iout in (2, ):    # XXX what to do with 3?
                varname = "spec%03d_pptv" % (i + 1)
            ncvar = self.nc.variables[varname]
            l.append(ncvar.long_name)
        return l

    @property
    def output_unit(self):
        if self.iout in (1, 3, 5):
            varname = "spec001_mr"
        if self.iout in (2, ):    # XXX what to do with 3?
            varname = "spec001_pptv"
        ncvar = self.nc.variables[varname]
        return ncvar.units

    @property
    def numpoint(self):
        return len(self.nc.dimensions['numpoint'])

    @property
    def numpointspec(self):
        return len(self.nc.dimensions['pointspec'])

    @property
    def numageclasses(self):
        return len(self.nc.dimensions['nageclass'])

    @property
    def numxgrid(self):
        return len(self.nc.dimensions['longitude'])

    @property
    def numygrid(self):
        return len(self.nc.dimensions['latitude'])

    @property
    def numzgrid(self):
        return len(self.nc.dimensions['height'])

    @property
    def longitude(self):
        return np.arange(self.outlon0,
                         self.outlon0 + (self.dxout * self.numxgrid),
                         self.dxout)

    @property
    def latitude(self):
        return np.arange(self.outlat0,
                         self.outlat0 + (self.dyout * self.numygrid),
                         self.dyout)

    @property
    def available_dates(self):
        loutstep = self.nc.loutstep
        nsteps = len(self.nc.dimensions['time'])
        if self.nc.ldirect < 0:
            # backward direction
            d = datetime.datetime.strptime(self.nc.iedate + self.nc.ietime,
                                           "%Y%m%d%H%M%S")
            return [(d + datetime.timedelta(seconds=t)).strftime("%Y%m%d%H%M%S")
                    for t in range(loutstep * (nsteps - 1), -loutstep, -loutstep)]
        else:
            # forward direction
            d = datetime.datetime.strptime(self.nc.ibdate + self.nc.ibtime,
                                           "%Y%m%d%H%M%S")
            return [(d + datetime.timedelta(seconds=t)).strftime("%Y%m%d%H%M%S")
                    for t in range(0, loutstep * nsteps, loutstep)]

    @property
    def ireleasestart(self):
        return self.nc.variables['RELSTART'][:]

    @property
    def ireleaseend(self):
        return self.nc.variables['RELEND'][:]

    @property
    def releasestart(self):
        if self.nc.ldirect < 0:
            rel_start = self.ireleasestart[::-1]
            d = datetime.datetime.strptime(self.nc.iedate + self.nc.ietime,
                                           "%Y%m%d%H%M%S")
            return [(d + datetime.timedelta(seconds=int(t))) for t in rel_start]
        else:
            rel_start = self.ireleasestart[:]
            d = datetime.datetime.strptime(self.nc.ibdate + self.nc.ibtime,
                                           "%Y%m%d%H%M%S")
            return [(d + datetime.timedelta(seconds=int(t))) for t in rel_start]

    @property
    def releaseend(self):
        if self.nc.ldirect < 0:
            rel_end = self.ireleaseend[::-1]
            d = datetime.datetime.strptime(self.nc.iedate + self.nc.ietime,
                                           "%Y%m%d%H%M%S")
            return [(d + datetime.timedelta(seconds=int(t))) for t in rel_end]
        else:
            rel_end = self.ireleaseend[:]
            d = datetime.datetime.strptime(self.nc.ibdate + self.nc.ibtime,
                                           "%Y%m%d%H%M%S")
            return [(d + datetime.timedelta(seconds=int(t))) for t in rel_end]


    @property
    def releasetimes(self):
        return [b - ((b - a) / 2)
                for a, b in zip(self.releasestart, self.releaseend)]

    @property
    def ORO(self):
        if 'ORO' in self.nc.variables:
            return self.nc.variables['ORO'][:].T
        else:
            return None

    @property
    def outheight(self):
        return self.nc.variables['height'][:].T

    @property
    def Heightnn(self):
        nx, ny, nz = (self.numxgrid, self.numygrid, self.numzgrid)
        outheight = self.outheight[:]
        if self.ORO is not None:
            oro = self.ORO[:]
            Heightnn = outheight + oro.reshape(nx, ny, 1)
        else:
            Heightnn = outheight.reshape(1, 1, nz)
        return Heightnn

    @property
    def zpoint1(self):
        return self.nc.variables['RELZZ1'][:].T

    @property
    def zpoint2(self):
        return self.nc.variables['RELZZ2'][:].T

    def __getitem__(self, key):
        return getattr(self, key)

    def keys(self):
        not_listed = ["keys", "fill_backward", "add_trajectory"]
        return [k for k in dir(self)
                if not k.startswith('_') and k not in not_listed]

    def fill_grids(self):
        return self.C

    def add_trajectory(self):
        """ see :func:`read_trajectories` """
        self.trajectory = reflexible.conv2netcdf4.read_trajectories(self)

    @property
    def options(self):
        # XXX Return a very minimalistic options dictionary.  To be completed.
        return {'readp': None}

    @property
    def FD(self):
        return FD(self.nc, self.nspec, self.species, self.available_dates,
                  self.direction, self.iout)

    @property
    def C(self):
        return C(self.nc, self.releasetimes, self.species, self.available_dates,
                 self.direction, self.iout, self.Heightnn, self.FD)

    def __init__(self, path=None):
        self.nc = nc.Dataset(path, 'r')


class FD(object):
    """Class that contains FD data indexed with (spec, date)."""

    def __init__(self, nc, nspec, species, available_dates, direction, iout):
        self.nc = nc
        self.nspec = nspec
        self.species = species
        self.available_dates = available_dates
        self.grid_dates = available_dates
        self.direction = direction
        self.iout = iout
        self._keys = [(s, k) for s, k in itertools.product(
            range(nspec), available_dates)]

    @property
    def keys(self):
        return self._keys()

    def __getitem__(self, item):
        nspec, date = item
        idate = self.available_dates.index(date)
        if self.iout in (1, 3, 5):
            varname = "spec%03d_mr" % (nspec + 1)
        if self.iout in (2,):    # XXX what to do with the 3 case?
            varname = "spec%03d_pptv" % (nspec + 1)
        fdc = FDC()
        fdc.grid = self.nc.variables[varname][:, :, idate, :, :, :].T
        fdc.itime = self.nc.variables['time'][idate]
        fdc.timestamp = datetime.datetime.strptime(
            self.available_dates[idate], "%Y%m%d%H%M%S")
        fdc.spec_i = nspec
        if self.direction == "forward":
            fdc.rel_i = 0
        else:
            fdc.rel_i = 'k'
        fdc.species = self.species
        # fdc.wet  # TODO
        # fdc.dry  # TODO
        return fdc


class C(object):
    """Class that contains C data indexed with (spec, date)."""

    def __init__(self, nc, releasetimes, species, available_dates,
                 direction, iout, Heightnn, FD):
        self.nc = nc
        self.nspec = len(nc.dimensions['numspec'])
        self.pointspec = len(nc.dimensions['pointspec'])
        self.releasetimes = releasetimes
        self.species = species
        self.available_dates = available_dates
        self.direction = direction
        self.iout = iout
        self.Heightnn = Heightnn
        self._FD = FD
        self._keys = [(s, k) for s, k in itertools.product(
            range(self.nspec), range(self.pointspec))]

    @property
    def keys(self):
        return self._keys()

    def __dir__(self):
        """ necessary for Ipython tab-completion """
        return self._keys

    def __iter__(self):
        return iter(self._keys)

    def __getitem__(self, item):
        """
        Calculates the 20-day sensitivity at each release point.

        This will cycle through all available_dates and create the filled
        array for each k in pointspec.

        Parameters
        ----------
        item : tuple
            A 2-element tuple specifying (nspec, pointspec)

        Return
        ------
        FDC instance
            An instance with grid, timestamp, species and other properties.

        Each element in the dictionary is a 3D array (x,y,z) for each species,k

        """
        assert type(item) is tuple and len(item) == 2
        nspec, pointspec = item
        assert type(nspec) is int and type(pointspec) is int

        if self.direction == 'backward':
            c = FDC()
            c.itime = None
            c.timestamp = self.releasetimes[pointspec]
            c.species = self.species[nspec]
            c.gridfile = 'multiple'
            c.rel_i = pointspec
            c.spec_i = nspec

            # read data grids and attribute/sum sensitivity
            if self.iout in (1, 3, 5):
                varname = "spec%03d_mr" % (nspec + 1)
            if self.iout in (2,):    # XXX what to do with the 3 case?
                varname = "spec%03d_pptv" % (nspec + 1)
            specvar = self.nc.variables[varname][:].T
            if True:
                c.grid = np.zeros((
                    len(self.nc.dimensions['longitude']),
                    len(self.nc.dimensions['latitude']),
                    len(self.nc.dimensions['height'])))
                for date in self.available_dates:
                    idate = self.available_dates.index(date)
                    # cycle through all the date grids
                    c.grid += specvar[:, :, :, idate, pointspec, :].sum(axis=-1)
            else:
                # Same than the above, but it comsumes more memory
                # Just let it here for future reference
                c.grid = specvar[:, :, :, :, pointspec, :].sum(axis=(-2, -1))
        else:
            # forward direction
            FD = self._FD
            d = FD.grid_dates[pointspec]
            c = FD[(nspec, d)]

        # add total column
        c.slabs = get_slabs(self.Heightnn, c.grid)

        return c


def get_slabs(Heightnn, grid):
    """Preps grid for plotting.

    Arguments
    ---------
    Heightnn : numpy array
      Height (outheight + topography).
    grid : numpy array
      A grid from the FLEXPARTDATA.

    Returns
    -------
    dictionary
      dictionary of rank-2 arrays corresponding to vertical levels.

    """
    normAreaHeight = True

    slabs = {}
    for i in range(grid.shape[2]):
        if normAreaHeight:
            data = grid[:, :, i] / Heightnn[:, :, i]
        else:
            data = grid[:, :, i]
        slabs[i + 1] = data.T    # XXX why?  something to do with http://en.wikipedia.org/wiki/ISO_6709 ?
    # first time sum to create Total Column
    slabs[0] = np.sum(grid, axis=2).T    # XXX why?  something to do with http://en.wikipedia.org/wiki/ISO_6709 ?
    return slabs


class FDC(object):
    """Data container for FD and C grids."""
    def __init__(self):
        self._keys = [
            'grid', 'gridfile', 'itime', 'timestamp', 'species', 'rel_i',
            'spec_i', 'dry', 'wet', 'slabs', 'shape', 'max', 'min']
        for key in self._keys:
            setattr(self, "_" + key, None)

    def keys(self):
        return self._keys

    @property
    def grid(self):
        return self._grid

    @grid.setter
    def grid(self, value):
        self._grid = value
        self._shape = value.shape
        self._max = value.max()
        self._min = value.min()

    @property
    def gridfile(self):
        return self._gridfile

    @gridfile.setter
    def gridfile(self, value):
        self._gridfile = value

    @property
    def itime(self):
        return self._itime

    @itime.setter
    def itime(self, value):
        self._itime = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = value

    @property
    def species(self):
        return self._species

    @species.setter
    def species(self, value):
        self._species = value

    @property
    def rel_i(self):
        return self._rel_i

    @rel_i.setter
    def rel_i(self, value):
        self._rel_i = value

    @property
    def spec_i(self):
        return self._spec_i

    @spec_i.setter
    def spec_i(self, value):
        self._spec_i = value

    @property
    def wet(self):
        """I'm the 'wet' property."""
        return self._wet

    @wet.setter
    def wet(self, value):
        self._wet = value

    @property
    def dry(self):
        return self._dry

    @dry.setter
    def dry(self, value):
        self._dry = value

    @property
    def slabs(self):
        return self._slabs

    @slabs.setter
    def slabs(self, value):
        self._slabs = value

    # Read-only properties
    @property
    def shape(self):
        return self._shape

    @property
    def max(self):
        return self._max

    @property
    def min(self):
        return self._min