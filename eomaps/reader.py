from functools import wraps
import numpy as np
from ._shapes import shapes

try:
    import pandas as pd

    _pd_OK = True
except ImportError:
    _pd_OK = False

try:
    import xarray as xar

    _xar_OK = True
except ImportError:
    _xar_OK = False

try:
    import rioxarray

    _rioxar_OK = True
except ImportError:
    _rioxar_OK = False


class read_file:
    """
    A collection of methods to read data from a file.
    (see individual reader-functions for details)

    Currently supported filetypes are:

    - NetCDF (requires `xarray`)
    - GeoTIFF (requires `rioxarray` + `xarray`)
    - CSV (requires `pandas`)

    """

    @staticmethod
    def GeoTIFF(path, crs_key=None, data_crs=None, sel=None, isel=None, set_data=None):
        """
        Read all relevant information necessary to add a GeoTIFF to the map.

        Use it as:

        >>> data = m.add_GeoTIFF(...)

        or

        >>> m.add_GeoTIFF(set_data=m)

        Parameters
        ----------
        path : str
            The path to the file.
        crs_key : str, optional
            The variable-name that holds the crs-information.

            By default the following options are tried:
            - <crs_key> = "spatial_ref", "crs"

              - crs = file.<crs_key>.attrs["crs_wkt"]
              - crs = file.<crs_key>.attrs["wkt"]
        data_crs : None, optional
            Optional way to specify the crs of the data explicitly.
            ("crs_key" will be ignored if "crs" is provided!)
        sel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.sel()`
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.sel.html)
            The default is None.
        isel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.isel()`.
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.isel.html)
            The default is {"band" : 0}  (if sel is None).
        set_data : None or eomaps.Maps
            Indicator if the dataset should be returned None or assigned to the
            provided Maps-object  (e.g. by using m.set_data(...)).
            The default is None.

        Returns
        -------
        dict (if set_data is False) or None (if set_data is True)
            A dict that contains the data required for plotting.

        """

        assert _xar_OK and _rioxar_OK, (
            "EOmaps: missing dependency for read_GeoTIFF: 'xarray' 'rioxarray'\n"
            + "To install, use 'conda install -c conda-forge xarray'"
            + "To install, use 'conda install -c conda-forge rioxarray'"
        )

        if isel is None and sel is None:
            isel = {"band": 0}

        with xar.open_dataset(path) as ncfile:
            if sel is not None:
                usencfile = ncfile.sel(**sel)
            elif isel is not None:
                usencfile = ncfile.isel(**isel)
            else:
                usencfile = ncfile

            dims = list(usencfile.dims)
            if len(dims) > 2:
                raise AssertionError(
                    "EOmaps: there are more than 2 dimensions! "
                    + "please select a specific dataset via the 'sel'- "
                    + f"or 'isel' kwargs. Available dimensionss: {dims}"
                )

            if data_crs is None:
                for crskey in ["spatial_ref", "crs"]:
                    if crskey in usencfile:
                        crsattr = usencfile[crskey].attrs
                        for wktkey in ["crs_wkt", "wkt"]:
                            if wktkey in crsattr:
                                data_crs = crsattr[wktkey]

            assert data_crs is not None, (
                "EOmaps: No crs information found... please specify the crs "
                + "via the 'data_crs' argument explicitly!"
            )

            data = usencfile.to_array().values
            xcoord, ycoord = np.meshgrid(
                getattr(usencfile, dims[0]).values, getattr(usencfile, dims[1]).values
            )

        if set_data is not None:
            set_data.set_data(data=data, xcoord=xcoord, ycoord=ycoord, crs=data_crs)
        else:
            return dict(data=data, xcoord=xcoord, ycoord=ycoord, crs=data_crs)

    @staticmethod
    def NetCDF(
        path,
        parameter=None,
        coords=None,
        crs_key=None,
        data_crs=None,
        sel=None,
        isel=None,
        set_data=None,
    ):
        """
        Read all relevant information necessary to add a NetCDF to the map.

        Use it as:

        >>> data = m.read_file.NetCDF(...)

        or

        >>> m.read_file.NetCDF(set_data=m)

        Parameters
        ----------
        path : str
            The path to the file.
        parameter : str
            The name of the variable to use as parameter.
            If None, the first variable of the NetCDF file will be used.
            The default is None.
        coords : tuple of str
            The names of the variables to use as x- and y- coordinates.
            (e.g. ('lat', 'lon'))
            The default is None in which case the coordinate-dimensions defined in the
            NetCDF will be used.
        crs_key : str, optional
            The attribute-name that holds the crs-information.

            By default the following options are tried:
            - <crs_key> = "spatial_ref", "crs", "crs_wkt"

              - crs = file.attrs.<crs_key>
        data_crs : None, optional
            Optional way to specify the crs of the data explicitly.
            ("crs_key" will be ignored if "data_crs" is provided!)
        sel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.sel()`
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.sel.html)
            The default is None.
        isel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.isel()`.
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.isel.html)
            The default is {"band" : 0}  (if sel is None).
        set_data : None or eomaps.Maps
            Indicator if the dataset should be returned None or assigned to the
            provided Maps-object  (e.g. by using m.set_data(...)).
            The default is None.

        Returns
        -------
        dict (if set_data is False) or None (if set_data is True)
            A dict that contains the data required for plotting.

        """

        assert _xar_OK, (
            "EOmaps: missing dependency for read_GeoTIFF: 'xarray'\n"
            + "To install, use 'conda install -c conda-forge xarray'"
        )

        with xar.open_dataset(path) as ncfile:
            if sel is not None:
                usencfile = ncfile.sel(**sel)
            elif isel is not None:
                usencfile = ncfile.isel(**isel)
            else:
                usencfile = ncfile

            if parameter is None:
                parameter = next(iter(ncfile))
                print(f"EOmaps: Using NetCDF variable '{parameter}' as parameter.")
            else:
                assert parameter in ncfile, (
                    f"EOmaps: The provided parameter-name '{parameter}' is not valid."
                    + f"Available parameters are {list(ncfile)}"
                )

            data = usencfile[parameter]

            if coords is None:
                coords = list(data.dims)
                if len(coords) != 2:
                    raise AssertionError(
                        "EOmaps: could not identify the coordinate-dimensions! "
                        + "Please provide coordinate-names explicitly via the "
                        + "'coords' kwarg.\n"
                        + f"Available coordinates: {list(usencfile.coords)}\n"
                        + f"Available variables: {list(ncfile)}"
                    )
                else:
                    print(f"EOmaps: Using NetCDF coordinates: {coords}")

            if data_crs is None:
                for crskey in ["spatial_ref", "crs", "crs_wkt"]:
                    if crskey in usencfile.attrs:
                        data_crs = usencfile.attrs[crskey]

            assert data_crs is not None, (
                "EOmaps: No crs information found... please specify the crs "
                + "via the 'data_crs' argument explicitly!"
            )

            if coords[0] in usencfile.coords:
                xcoord = usencfile.coords[coords[0]]
            elif coords[0] in usencfile:
                xcoord = usencfile[coords[0]]
            else:
                raise AssertionError(
                    f"EOmaps: Coordinate '{coords[0]}' is not present in the NetCDF.\n"
                    + f"Available coordinates: {list(usencfile.coords)}\n"
                    + f"Available variables: {list(ncfile)}"
                )

            if coords[1] in usencfile.coords:
                ycoord = usencfile.coords[coords[1]]
            elif coords[1] in usencfile:
                ycoord = usencfile[coords[1]]
            else:
                raise AssertionError(
                    f"EOmaps: Coordinate '{coords[1]}' is not present in the NetCDF\n"
                    + f"Available coordinates: {list(usencfile.coords)}\n"
                    + f"Available variables: {list(ncfile)}"
                )

            if data.dims != xcoord.dims or data.dims != xcoord.dims:
                raise AssertionError(
                    "EOmaps: Invalid dimensions of data and coordinates!\n"
                    + f"data: {data.dims},  xcoord: {xcoord.dims}, ycoord: {ycoord.dims}"
                )

            # xcoord, ycoord = np.meshgrid(
            #     usencfile.coords[coords[0]].values, usencfile.coords[coords[1]].values
            # )

        if set_data is not None:
            set_data.set_data(
                data=data.values,
                xcoord=xcoord.values,
                ycoord=ycoord.values,
                crs=data_crs,
                parameter=parameter,
            )
        else:
            return dict(
                data=data.values,
                xcoord=xcoord.values,
                ycoord=ycoord.values,
                crs=data_crs,
                parameter=parameter,
            )

    @staticmethod
    def CSV(
        path,
        parameter=None,
        xcoord=None,
        ycoord=None,
        crs=None,
        set_data=None,
        **kwargs,
    ):
        """
        Read all relevant information necessary to add a CSV-file to the map.

        Use it as:

        >>> data = m.read_file.CSV(...)

        or

        >>> m.read_file.CSV(set_data=m)

        Parameters
        ----------
        path : str
            The path to the csv-file.
        parameter : str
            The column-name to use as parameter.
        xcoord : str
            The column-name to use as xcoord.
        ycoord : str
            The column-name to use as ycoord.
        crs : crs-identifier
            The crs of the data. (see "Maps.set_data" for details)

        kwargs :
            additional kwargs passed to `pandas.read_csv`.

        Returns
        -------
        dict (if set_data is False) or None (if set_data is True)
            A dict that contains the data required for plotting.

        """
        assert _pd_OK, (
            "EOmaps: missing dependency for read_csv: 'pandas'\n"
            + "To install, use 'conda install -c conda-forge pandas'"
        )

        data = pd.read_csv(path, **kwargs)

        for key in [parameter, xcoord, ycoord]:
            assert key in data, (
                f"EOmaps: the parameter-name {key} is not a column of the csv-file!\n"
                + f"Available columns are: {list(data)}"
            )

        if set_data is not None:
            set_data.set_data(
                data=data[[parameter, xcoord, ycoord]],
                xcoord=xcoord,
                ycoord=ycoord,
                crs=crs,
                parameter=parameter,
            )
        else:
            return dict(
                data=data[[parameter, xcoord, ycoord]],
                xcoord=xcoord,
                ycoord=ycoord,
                crs=crs,
                parameter=parameter,
            )


def _from_file(
    data,
    crs=None,
    shape=None,
    plot_specs=None,
    classify_specs=None,
    val_transform=None,
    coastline=True,
    parent=None,
    figsize=None,
    layer=0,
    **kwargs,
):
    """
    Convenience function to initialize a new Maps-object from a file.

    EOmaps will try several attempts to plot the data (fastest first).

    - fist, shading as a raster is used: `m.set_shape.shade_raster`
    - if it fails, shading with points is used: `m.set_shape.shade_raster`
    - if it fails, ordinary ellipse-plot is created: `m.set_shape.ellipses`


    This function is (in principal) a shortcut for:

        >>> m = Maps(crs=..., layer=...)
        >>> m.set_data(**m.read_GeoTIFF(...))
        >>> m.set_plot_specs(...)
        >>> m.set_classify_specs(...)
        >>> m.plot_map(...)

    Parameters
    ----------
    path : str
        The path to the GeoTIFF file.
    crs : any, optional
        The plot-crs. A crs-identifier usable with cartopy.
        The default is None, in which case the crs of the GeoTIFF is used if
        possible, else epsg=4326.
    sel : dict, optional
        A dict of keyword-arguments passed to `xarray.Dataset.sel()`
        The default is {"band": 0}.
    isel : dict, optional
        A dict of keyword-arguments passed to `xarray.Dataset.isel()`.
        The default is None.
    plot_specs : dict, optional
        A dict of keyword-arguments passed to `m.set_plot_specs()`.
        The default is None.
    classify_specs : dict, optional
        A dict of keyword-arguments passed to `m.set_classify_specs()`.
        The default is None.
    val_transform : None or callable
        A function that is used to transform the data-values.
        (e.g. to apply scaling etc.)

        >>> def val_transform(a):
        >>>     return a / 10
    coastline: bool
        Indicator if a coastline should be added or not.
        The default is True
    parent : eomaps.Maps
        The parent Maps object to use (e.g. `parent.new_layer()` will be used
        to create a Maps-object for the dataset)
    figsize : tuple, optional
        The size of the figure. (Only relevant if parent is None!)
    kwargs :
        Keyword-arguments passed to `m.shade_map()`
    Returns
    -------
    m : eomaps.Maps
        The created Maps object.

    """
    from . import Maps  # do this here to avoid circular imports

    if val_transform:
        data["data"] = val_transform(data["data"])

    if parent is not None:
        m = parent.new_layer(
            copy_data_specs=False,
            copy_plot_specs=False,
            copy_classify_specs=False,
            copy_shape=False,
            layer=layer,
        )
    else:
        # get crs from file
        if crs is None:
            crs = data.get("crs", None)
        # try if it's possible to initialize a Maps-object with the file crs
        try:
            m = Maps._get_cartopy_crs(crs=crs)
        except Exception:
            crs = 4326
            print(f"EOmaps: could not use native crs... defaulting to epsg={crs}.")

        m = Maps(crs=crs, figsize=figsize)

    if coastline:
        m.add_feature.preset.coastline()

    m.set_data(**data)
    if plot_specs:
        m.set_plot_specs(**plot_specs)
    if classify_specs:
        m.set_classify_specs(**classify_specs)

    if shape is not None:
        # use the provided shape
        if isinstance(shape, str):
            getattr(m.set_shape, shape)()
        elif isinstance(shape, dict):
            getattr(m.set_shape, shape.pop("shape"))(**shape)

        m.plot_map(**kwargs)
        return m

    else:
        # try to plot as raster - shading...
        try:
            m.set_shape.shade_raster()
            m.plot_map(**kwargs)
            return m
        except Exception:
            pass

        # try to plot as point - shading...
        try:
            m.set_shape.shade_points()
            m.plot_map(**kwargs)
            return m
        except Exception:
            pass

        # try to plot as ellipses
        m.set_shape.ellipses()
        m.plot_map(**kwargs)

    return m


class from_file:
    """
    A collection of methods to initialize a new Maps-object from a file.
    (see individual reader-functions for details)

    Currently supported filetypes are:

    - NetCDF (requires `xarray`)
    - GeoTIFF (requires `rioxarray` + `xarray`)
    - CSV (requires `pandas`)
    """

    @staticmethod
    def NetCDF(
        path,
        parameter=None,
        coords=None,
        data_crs_key=None,
        data_crs=None,
        sel=None,
        isel=None,
        plot_crs=None,
        shape=None,
        plot_specs=None,
        classify_specs=None,
        val_transform=None,
        coastline=True,
        **kwargs,
    ):
        """
        Convenience function to initialize a new Maps-object from a NetCDF file.

        If no explicit shape is provided, EOmaps will try several attempts to plot
        the data (fastest first).

        - fist, shading as a raster is used: `m.set_shape.shade_raster`
        - if it fails, shading with points is used: `m.set_shape.shade_raster`
        - if it fails, ordinary ellipse-plot is created: `m.set_shape.ellipses`

        This function is (in principal) a shortcut for:

        >>> m = Maps(crs=...)
        >>> m.set_data(**m.read_file.NetCDF(...))
        >>> m.set_plot_specs(...)
        >>> m.set_classify_specs(...)
        >>> m.plot_map(...)


        Parameters
        ----------
        path : str
            The path to the NetCDF file.
        parameter : str, optional
            The name of the variable to use as parameter.
            If None, the first variable of the NetCDF file will be used.
            The default is None.
        coords : tuple of str
            The names of the variables to use as x- and y- coordinates.
            (e.g. ('lat', 'lon'))
            The default is None in which case the coordinate-dimensions defined in the
            NetCDF will be used.
        data_crs_key : str, optional
            The attribute-name that holds the crs-information.

            By default the following options are tried:
            - <crs_key> = "spatial_ref", "crs", "crs_wkt"

              - crs = file.attrs.<crs_key>

        data_crs : None, optional
            Optional way to specify the crs of the data explicitly.
            ("data_crs_key" will be ignored if "data_crs" is provided!)
        sel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.sel()`
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.sel.html)
            The default is None.
        isel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.isel()`.
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.isel.html)
            The default is {"band" : 0}  (if sel is None).
        plot_crs : any, optional
            The plot-crs. A crs-identifier usable with cartopy.
            The default is None, in which case the crs of the GeoTIFF is used if
            possible, else epsg=4326.
        shape : str, dict or None, optional
            - if str: The name of the shape to use, e.g. one of:
              ['geod_circles', 'ellipses', 'rectangles', 'voroni_diagram',
              'delaunay_triangulation', 'shade_points', 'shade_raster']
            - if dict: a dictionary with parameters passed to the selected shape.
              The dict MUST contain a key "shape" that holds the name of the shape!

              >>> dict(shape="rectangles", radius=1, radius_crs=.5)

        plot_specs : dict, optional
            A dict of keyword-arguments passed to `m.set_plot_specs()`.
            The default is None.
        classify_specs : dict, optional
            A dict of keyword-arguments passed to `m.set_classify_specs()`.
            The default is None.
        val_transform : None or callable
            A function that is used to transform the data-values.
            (e.g. to apply scaling etc.)

            >>> def val_transform(a):
            >>>     return a / 10
        coastline: bool
            Indicator if a coastline should be added or not.
            The default is True
        kwargs :
            Keyword-arguments passed to `m.plot_map()`
        Returns
        -------
        m : eomaps.Maps
            The created Maps object.

        """

        assert _xar_OK, (
            "EOmaps: missing dependency for read_NetCDF: 'xarray'\n"
            + "To install, use 'conda install -c conda-forge xarray'"
        )

        # read data
        data = read_file.NetCDF(
            path,
            parameter=parameter,
            coords=coords,
            crs_key=data_crs_key,
            data_crs=data_crs,
            sel=sel,
            isel=isel,
            set_data=None,
        )

        if val_transform:
            data["data"] = val_transform(data["data"])

        return _from_file(
            data,
            crs=plot_crs,
            shape=shape,
            plot_specs=plot_specs,
            classify_specs=classify_specs,
            val_transform=val_transform,
            coastline=coastline,
            **kwargs,
        )

    @staticmethod
    def GeoTIFF(
        path,
        data_crs_key=None,
        data_crs=None,
        sel=None,
        isel=None,
        plot_crs=None,
        shape=None,
        plot_specs=None,
        classify_specs=None,
        val_transform=None,
        coastline=True,
        **kwargs,
    ):
        """
        Convenience function to initialize a new Maps-object from a GeoTIFF file.

        If no explicit shape is provided, EOmaps will try several attempts to plot
        the data (fastest first).

        - fist, shading as a raster is used: `m.set_shape.shade_raster`
        - if it fails, shading with points is used: `m.set_shape.shade_raster`
        - if it fails, ordinary ellipse-plot is created: `m.set_shape.ellipses`

        This function is (in principal) a shortcut for:

        >>> m = Maps(crs=...)
        >>> m.set_data(**m.read_file.GeoTIFF(...))
        >>> m.set_plot_specs(...)
        >>> m.set_classify_specs(...)
        >>> m.plot_map(...)

        Parameters
        ----------
        path : str
            The path to the GeoTIFF file.
        data_crs_key : str, optional
            The variable-name that holds the crs-information.

            By default the following options are tried:
            - <crs_key> = "spatial_ref", "crs"

              - crs = file.<crs_key>.attrs["crs_wkt"]
              - crs = file.<crs_key>.attrs["wkt"]
        data_crs : None, optional
            Optional way to specify the crs of the data explicitly.
            ("data_crs_key" will be ignored if "data_crs" is provided!)
        sel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.sel()`
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.sel.html)
            The default is None.
        isel : dict, optional
            A dictionary of keyword-arguments passed to `xarray.Dataset.isel()`.
            (see https://xarray.pydata.org/en/stable/generated/xarray.Dataset.isel.html)
            The default is {"band" : 0}  (if sel is None).
        plot_crs : any, optional
            The plot-crs. A crs-identifier usable with cartopy.
            The default is None, in which case the crs of the GeoTIFF is used if
            possible, else epsg=4326.
        shape : str, dict or None, optional
            - if str: The name of the shape to use, e.g. one of:
              ['geod_circles', 'ellipses', 'rectangles', 'voroni_diagram',
              'delaunay_triangulation', 'shade_points', 'shade_raster']
            - if dict: a dictionary with parameters passed to the selected shape.
              The dict MUST contain a key "shape" that holds the name of the shape!

              >>> dict(shape="rectangles", radius=1, radius_crs=.5)

        plot_specs : dict, optional
            A dict of keyword-arguments passed to `m.set_plot_specs()`.
            The default is None.
        classify_specs : dict, optional
            A dict of keyword-arguments passed to `m.set_classify_specs()`.
            The default is None.
        val_transform : None or callable
            A function that is used to transform the data-values.
            (e.g. to apply scaling etc.)

            >>> def val_transform(a):
            >>>     return a / 10
        coastline: bool
            Indicator if a coastline should be added or not.
            The default is True
        kwargs :
            Keyword-arguments passed to `m.plot_map()`
        Returns
        -------
        m : eomaps.Maps
            The created Maps object.

        """

        assert _xar_OK and _rioxar_OK, (
            "EOmaps: missing dependency for read_GeoTIFF: 'xarray' 'rioxarray'\n"
            + "To install, use 'conda install -c conda-forge xarray'"
            + "To install, use 'conda install -c conda-forge rioxarray'"
        )

        # read data
        data = read_file.GeoTIFF(
            path,
            sel=sel,
            isel=isel,
            set_data=None,
            data_crs=data_crs,
            crs_key=data_crs_key,
        )

        if val_transform:
            data["data"] = val_transform(data["data"])

        return _from_file(
            data,
            crs=plot_crs,
            shape=shape,
            plot_specs=plot_specs,
            classify_specs=classify_specs,
            val_transform=val_transform,
            coastline=coastline,
            **kwargs,
        )

    @staticmethod
    def CSV(
        path=None,
        parameter=None,
        xcoord=None,
        ycoord=None,
        data_crs=None,
        plot_crs=None,
        shape=None,
        plot_specs=None,
        classify_specs=None,
        val_transform=None,
        coastline=True,
        **kwargs,
    ):
        """
        Convenience function to initialize a new Maps-object from a CSV file.

        If no explicit shape is provided, EOmaps will try several attempts to plot
        the data (fastest first).

        - fist, shading as a raster is used: `m.set_shape.shade_raster`
        - if it fails, shading with points is used: `m.set_shape.shade_raster`
        - if it fails, ordinary ellipse-plot is created: `m.set_shape.ellipses`

        This function is (in principal) a shortcut for:

        >>> m = Maps(crs=...)
        >>> m.set_data(**m.read_file.CSV(...))
        >>> m.set_plot_specs(...)
        >>> m.set_classify_specs(...)
        >>> m.plot_map(...)


        Parameters
        ----------
        path : str
            The path to the csv-file.
        parameter : str
            The column-name to use as parameter.
        xcoord : str
            The column-name to use as xcoord.
        ycoord : str
            The column-name to use as ycoord.
        data_crs : crs-identifier
            The crs of the data. (see "Maps.set_data" for details)
        plot_crs : any, optional
            The plot-crs. A crs-identifier usable with cartopy.
            The default is None, in which case the crs of the GeoTIFF is used if
            possible, else epsg=4326.
        shape : str, dict or None, optional
            - if str: The name of the shape to use, e.g. one of:
              ['geod_circles', 'ellipses', 'rectangles', 'voroni_diagram',
              'delaunay_triangulation', 'shade_points', 'shade_raster']
            - if dict: a dictionary with parameters passed to the selected shape.
              The dict MUST contain a key "shape" that holds the name of the shape!

              >>> dict(shape="rectangles", radius=1, radius_crs=.5)

        plot_specs : dict, optional
            A dict of keyword-arguments passed to `m.set_plot_specs()`.
            The default is None.
        classify_specs : dict, optional
            A dict of keyword-arguments passed to `m.set_classify_specs()`.
            The default is None.
        val_transform : None or callable
            A function that is used to transform the data-values.
            (e.g. to apply scaling etc.)

            >>> def val_transform(a):
            >>>     return a / 10
        coastline: bool
            Indicator if a coastline should be added or not.
            The default is True
        kwargs :
            Keyword-arguments passed to `m.plot_map()`

        Returns
        -------
        m : eomaps.Maps
            The created Maps object.

        """

        # read data
        data = read_file.CSV(
            path=path,
            parameter=parameter,
            xcoord=xcoord,
            ycoord=ycoord,
            crs=data_crs,
        )

        return _from_file(
            data,
            crs=plot_crs,
            shape=shape,
            plot_specs=plot_specs,
            classify_specs=classify_specs,
            val_transform=val_transform,
            coastline=coastline,
            **kwargs,
        )


class new_layer_from_file:
    """
    A collection of methods to add a new layer to an existing Maps-object from a file.
    (see individual reader-functions for details)

    Currently supported filetypes are:

    - NetCDF (requires `xarray`)
    - GeoTIFF (requires `rioxarray` + `xarray`)
    - CSV (requires `pandas`)
    """

    # assign a parent maps-object and call m.new_layer instead of creating a new one.
    def __init__(self, m):
        self._m = m

    @wraps(from_file.NetCDF)
    def NetCDF(self, *args, **kwargs):
        return from_file.NetCDF(*args, **kwargs, parent=self._m)

    @wraps(from_file.GeoTIFF)
    def GeoTIFF(self, *args, **kwargs):
        return from_file.GeoTIFF(*args, **kwargs, parent=self._m)

    @wraps(from_file.CSV)
    def CSV(self, *args, **kwargs):
        return from_file.CSV(*args, **kwargs, parent=self._m)