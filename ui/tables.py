"""Tabela de drill-down em AgGrid com formatação condicional por status de severidade."""

from st_aggrid import AgGrid, ColumnsAutoSizeMode, GridOptionsBuilder, JsCode

_CELL_STYLE = JsCode("""
function(params){
  if(params.data.status === 'vermelho') return {'backgroundColor':'#FDECEA','color':'#B71C1C'};
  if(params.data.status === 'amarelo') return {'backgroundColor':'#FFF8E1','color':'#7A5B00'};
  return {'backgroundColor':'#F2FBF5','color':'#1B5E20'};
}
""")


def tabela_drilldown(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_default_column(sortable=True, filter=True, resizable=True)
    gb.configure_column("Data", type=["dateColumnFilter"], valueFormatter="value ? new Date(value).toLocaleDateString('pt-BR') : ''")
    gb.configure_column("Justificativa", minWidth=260)
    gb.configure_column("status", hide=True)

    grid_options = gb.build()
    for col in grid_options["columnDefs"]:
        if col["field"] != "status":
            col["cellStyle"] = _CELL_STYLE

    return AgGrid(
        df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        theme="balham",
        height=420,
    )
