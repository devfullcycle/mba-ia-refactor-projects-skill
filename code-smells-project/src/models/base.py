def row_to_dict(row, campos):
    return {campo: row[campo] for campo in campos}
