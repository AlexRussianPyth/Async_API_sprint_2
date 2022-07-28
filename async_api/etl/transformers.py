from validation import EsFilmwork, EsGenre, EsPerson


class FilmTransformer:
    """Преобразует данные из Postgre в подходящий для Elastic формат.
    Inputs: Batch of records from Postgre
    Outpur: Batch of docs in elasticsearch format
    """

    def transform_record(self, records: list) -> list[EsFilmwork]:
        """Преобразует список записей из БД в валидированный список EsFilmwork классов"""
        validated_records = []

        for record in records:

            actors = []
            if record['actors']:
                for actor in record['actors']:
                    actor_id, actor_name = actor.strip(',').split('|')
                    actors.append({
                        'id': actor_id,
                        'name': actor_name
                    })

            writers = []
            if record['writers']:
                for writer in record['writers']:
                    writer_id, writer_name = writer.strip(',').split('|')
                    writers.append({
                        'id': writer_id,
                        'name': writer_name
                    })

            record_dict = {
                "id": record['filmwork_id'],
                "imdb_rating": record['rating'],
                "genre": record['genre'],
                "title": record['title'],
                "description": record['description'],
                "director": record['director'] if record['director'] is not None else [],
                "actors_names": record['actors_names'],
                "writers_names": record['writers_names'],
                "actors": actors,
                "writers": writers,
            }

            validated_records.append(EsFilmwork(**record_dict))

        return validated_records


class GenreTransformer:
    """Преобразует данные из Postgre в подходящий для Elastic формат жанра.
    Inputs: Batch of records from Postgre
    Outpur: Batch of docs in elasticsearch format
    """

    def transform_record(self, records: list) -> list[EsGenre]:
        """Преобразует список записей из БД в валидированный список EsGenre классов"""
        validated_records = []

        for record in records:
            record_dict = {
                'id': record['id'],
                'name': record['name'],
            }

            validated_records.append(EsGenre(**record_dict))

        return validated_records


class PersonTransformer:
    """Преобразует данные из Postgre в подходящий для Elastic формат человека.
    Inputs: Batch of records from Postgre
    Outpur: Batch of docs in elasticsearch format
    """

    def transform_record(self, records: list) -> list[EsPerson]:
        """Преобразует список записей из БД в валидированный список EsPerson классов"""
        validated_records = []

        for record in records:
            record_dict = {
                'id': record['id'],
                'full_name': record['full_name'],
                'role': record['role'],
            }

            validated_records.append(EsPerson(**record_dict))

        return validated_records
