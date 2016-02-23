# -*- coding: utf-8 -*-

try:
    import pandas as pd
except ImportError:
    pd = None


if pd:
    import numpy as np
    from . import ConverterAccessor, Options

    class PandasDataFrameConverter(ConverterAccessor):

        writes_types = pd.DataFrame

        @classmethod
        def base_reader(cls, options):
            return (
                super(PandasDataFrameConverter, cls).base_reader(
                    Options(options)
                    .override(ndim=2)
                )
            )

        @classmethod
        def read_value(cls, value, options):
            index = options.get('index', 1)
            header = options.get('header', 1)
            dtype = options.get('dtype', None)
            copy = options.get('copy', False)

            value = np.array(value, dtype=object)  # object array to prevent str arrays

            columns = pd.MultiIndex.from_arrays(value[:header, index:]) if header > 0 else None
            ix_names = value[header-1, :index] if (header and index) else None
            ix = pd.MultiIndex.from_arrays(value[header:, :index].T,
                                           names=ix_names) if index > 0 else None
            return pd.DataFrame(value[header:, index:].tolist(), index=ix, columns=columns, dtype=dtype, copy=copy)

        @classmethod
        def write_value(cls, value, options):
            index = options.get('index', True)
            header = options.get('header', True)

            index_names = value.index.names
            index_names = ['' if i is None else i for i in index_names]
            index_levels = len(index_names)

            if index:
                if value.index.name in value.columns:
                    # Prevents column name collision when resetting the index
                    value.index.rename(None, inplace=True)
                value = value.reset_index()

            if header:
                if isinstance(value.columns, pd.MultiIndex):
                    columns = list(zip(*value.columns.tolist()))
                    columns = [list(i) for i in columns]
                    # Move index names right above the index
                    if index:
                        for c in columns[:-1]:
                            c[:index_levels] = [''] * index_levels
                        columns[-1][:index_levels] = index_names
                else:
                    columns = [value.columns.tolist()]
                    if index:
                        columns[0][:index_levels] = index_names
                value = columns + value.values.tolist()
            else:
                value = value.values.tolist()

            return value


    PandasDataFrameConverter.install_for(pd.DataFrame)


    class PandasSeriesConverter(ConverterAccessor):

        writes_types = pd.Series

        @classmethod
        def read_value(cls, value, options):
            index = options.get('index', 1)
            header = options.get('header', True)
            dtype = options.get('dtype', None)
            copy = options.get('copy', False)

            if header:
                columns = value[0]
                if not isinstance(columns, list):
                    columns = [columns]
                data = value[1:]
            else:
                columns = None
                data = value

            df = pd.DataFrame(data, columns=columns, dtype=dtype, copy=copy)

            if index:
                df = df.set_index(list(df)[0:index])

            series = df.squeeze()

            if not header:
                series.name = None
                series.index.name = None

            return series

        @classmethod
        def write_value(cls, value, options):

            index_names = value.index.names
            index_names = ['' if i is None else i for i in index_names]

            if all(v is None for v in value.index.names) and value.name is None:
                default_header = False
            else:
                default_header = True

            index = options.get('index', True)
            header = options.get('header', default_header)

            if index:
                rv = value.reset_index().values.tolist()
                header_row = [index_names + [value.name]]
            else:
                rv = value.values[:, np.newaxis].tolist()
                header_row = [[value.name]]
            if header:
                    rv = header_row + rv

            return rv


    PandasSeriesConverter.install_for(pd.Series)
