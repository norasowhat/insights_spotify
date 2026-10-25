from pyspark.sql import SparkSession
from pyspark.sql import functions as F

print("Iniciando sesión de Spark para el equipo (Nora + Fernando)...")

spark = SparkSession.builder \
    .appName("Spotify_Data_Cleaning_Team") \
    .getOrCreate()

input_path = "/data"

print("Cargando archivos JSON de todo el equipo...")
# Nota: Pasamos `input_path` directamente sin `/*.json` para que busque recursivamente en subcarpetas
df_raw = spark.read.option("multiline", "true") \
    .option("recursiveFileLookup", "true") \
    .json(input_path)

print("Limpiando datos y asignando identificador de usuario...")
df_cleaned = df_raw.filter(F.col("master_metadata_track_name").isNotNull()) \
    .filter(F.col("ms_played") >= 5000) \
    .withColumn(
        "user",
        F.when(F.input_file_name().contains("datafernando"), "Fernando")
         .when(F.input_file_name().contains("datanora"), "Nora")
         .otherwise("Otro")
    ) \
    .withColumn("ts_timestamp", F.to_timestamp(F.col("ts"))) \
    .withColumn("date", F.to_date(F.col("ts_timestamp"))) \
    .withColumn("hour", F.hour(F.col("ts_timestamp"))) \
    .withColumn("minutes_played", F.round(F.col("ms_played") / 60000, 2)) \
    .withColumn("country", F.col("conn_country")) \
    .select(
        F.col("user"),
        F.col("ts_timestamp").alias("played_at"),
        F.col("date"),
        F.col("hour"),
        F.col("master_metadata_track_name").alias("track_name"),
        F.col("master_metadata_album_artist_name").alias("artist_name"),
        F.col("master_metadata_album_album_name").alias("album_name"),
        F.col("ms_played"),
        F.col("minutes_played"),
        F.col("reason_start"),
        F.col("reason_end"),
        F.col("shuffle"),
        F.col("skipped"),
        F.col("conn_country").alias("country"),
        F.col("platform")
    )

output_path = "/app/spotify_history_cleaned.parquet"
print(f"Guardando resultado unificado en {output_path}...")

df_cleaned.write.mode("overwrite").parquet(output_path)

print("¡Proceso completado con éxito! Archivo Parquet unificado para Nora y Fernando.")