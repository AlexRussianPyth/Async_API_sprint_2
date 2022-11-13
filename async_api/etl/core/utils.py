def ornate_ids(ids_list) -> str:
    """Приводит лист с ID к удобному формату для запросов в Postgre:
    'id', 'id', ...
    """

    quoted_list = ["'" + id + "'" for id in ids_list]
    id_string = ",".join(quoted_list)

    return id_string
