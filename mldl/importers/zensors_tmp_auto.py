import psycopg2
import psycopg2.extras
import questionary
import os
from os.path import isfile
from uuid import UUID
from fabric.connection import Connection

from typing import Sequence

from mldl.printer import pprint
from mldl.importers.zensors_tmp import run as run_zensors
from mldl.importers.server import run as run_server

def main():
	pg_pass = os.getenv("PROD_PG_PASS")
	tms_pass = os.getenv("PROD_TMS_PASS")

	if pg_pass is None:
		pprint("{bold}{red}FATAL: Missing the {yellow}PROD_PG_PASS{red} environment variable")
		return

	if tms_pass is None:
		pprint("{bold}{red}FATAL: Missing the {yellow}PROD_TMS_PASS{red} environment variable")
		return

	sensor_uid = get_text("Input the sensor uid:")

	if sensor_uid is None:
		return

	pprint("{cyan}Loading sensor information from main db...")

	with Connection("zprod").forward_local(local_port = 6432, remote_host = "zensorsproductiondb.clsnnlioasfe.us-east-2.rds.amazonaws.com", remote_port = 5432):
		try:
			with psycopg2.connect(f"host=localhost port=6432 user=zensorsproduser dbname=zensors password={pg_pass}") as connection:
				with connection.cursor() as cursor:
					sensor_data = cursor.execute("""
						SELECT
							sensor.uid as sensor_uid,
							sensor.id as sensor_id,
							sensor.name as sensor_name,
							sensor.crop_area as sensor_mask,
							device.uid as device_uid,
							question.sensor_type as question_type
						FROM sensor
							JOIN device ON sensor.device_id = device.id
							JOIN question ON question.id = sensor.question_id
						WHERE sensor.uid = %s
					""", [sensor_uid])
					sensor_data = cursor.fetchone()
					if sensor_data is None:
						pprint("{bold}{red}FATAL: No sensor with that uid found")
						return
		except Exception as e:
			pprint("{bold}{red}FATAL: Failed to fetch sensor data")
			raise e

	sensor_uid, sensor_id, sensor_name, sensor_mask, device_uid, question_type = sensor_data

	print()
	pprint("{cyan}Found the following information for this sensor:")
	print()
	pprint("  {yellow}Sensor UID {clear}  {value}", value = sensor_uid)
	pprint("  {yellow}Sensor ID  {clear}  {value}", value = sensor_id)
	pprint("  {yellow}Sensor Name{clear}  {value}", value = sensor_name)
	pprint("  {yellow}Sensor Mask{clear}  {value}", value = sensor_mask)
	pprint("  {yellow}Device UID {clear}  {value}", value = device_uid)
	pprint("  {yellow}Sensor Type{clear}  {value}", value = question_type)
	print()

	if question_type != "COUNT":
		pprint("{bold}{red}FATAL: only {yellow}COUNT{red} sensors can be imported")
		return

	import_name = get_text("What name do you want to use for this import?")
	csv_path = f"{import_name}.csv"
	tar_path = f"{import_name}.tar.gz"

	if not isfile(csv_path) or get_selection("The *.csv file for this import already exists; would you like to skip exporting from the db and use it instead?", ["Yes", "No"]) == "No":
		print()
		pprint("{cyan}Dumping annotations from timescale...")

		with Connection("timescale").forward_local(local_port = 6432, remote_host = "localhost", remote_port = 5432):
			try:
				with psycopg2.connect(f"host=localhost port=6432 user=zensors dbname=zensors password={tms_pass}") as connection:
					with connection.cursor() as cursor:
						cursor.execute("""
							CREATE TEMPORARY TABLE export ON COMMIT DROP AS
							SELECT
								sl.sensor_id,
								sl.event_time,
								sl.labeler_id,
								coalesce(sl.bounding_boxes, array[]::box[]) AS bounding_boxes,
								sp.value->>0 as image_url
							FROM sensor_label sl
								JOIN stream_point sp
									ON sl.event_time = sp.event_time
							WHERE sl.sensor_id = %s
								AND sp.stream_id = %s
								AND sl.labeler_type = 'WORKER'
								AND NOT EXISTS (SELECT * FROM sensor_label_mldl_import slmi WHERE slmi.sensor_id = sl.sensor_id AND slmi.event_time = sl.event_time AND slmi.labeler_id = sl.labeler_id::uuid);
						""", [sensor_id, device_uid])

						with open(csv_path, "w") as csv_file:
							cursor.copy_expert("COPY export TO STDOUT CSV HEADER", csv_file)

						with open(csv_path, "r") as csv_file:
							pprint("{green}Dumped {count} annotations.", count = len(csv_file.readlines()) - 1)

						cursor.execute("""
							INSERT INTO sensor_label_mldl_import (sensor_id, event_time, labeler_id)
							SELECT sensor_id, event_time, labeler_id::uuid
							FROM export
						""")

						connection.commit()
			except Exception as e:
				pprint("{bold}{red}FATAL: Failed to fetch annotations")
				raise e

		pprint("{cyan}Done.")
		print()

	if not isfile(tar_path) or get_selection("The *.tar.gz file for this import already exists; would you like to skip the zensors_tmp importer?", ["Yes", "No"]) == "No":
		if get_selection("Would you like to ignore the stored mask and instead use the entire image?", ["No, use the stored mask", "Yes, use the entire image"]) == "Yes, use the entire image":
			sensor_mask = None

		class_name = get_text("What class does this sensor annotate?")
		data_source_name = get_text("What name would you like to use for the data source?", default = sensor_name) + f" (Zensors {sensor_id})"

		print()
		pprint("{cyan}Running {yellow}mldl.importers.zensors_tmp{cyan} import job...")

		run_zensors(
			n_workers = 4,
			labels = csv_path,
			class_name = class_name,
			camera_uid = device_uid,
			data_source_name = data_source_name,
			output = tar_path,
			mask = sensor_mask,
			sensor_uid = UUID(sensor_uid)
		)
		pprint("{cyan}Done.")
		print()

	if get_selection("Would you like to proceed with the server import?", ["Yes", "No"]) == "No":
		return

	pprint("{cyan}Transferring and unzipping the tar...")

	with Connection("mldl") as mldl:
		remote_path = f"/media/nvme/neo4j/import/zensors/{import_name}"
		remote_tar_path = f"/tmp/{import_name}.tar.gz"
		mldl.put(tar_path, remote_tar_path)
		mldl.run(f"mkdir -p {remote_path}")
		mldl.run(f"tar -C {remote_path} -xf {remote_tar_path}")
		mldl.run(f"rm {remote_tar_path}")

	pprint("{cyan}Done.")

	print()
	pprint("{cyan}Running server import...")

	run_server(
		local_tar = tar_path,
		server_path = f"zensors/{import_name}",
		n_workers = 1,
		threads_per_worker = os.cpu_count()
	)

	pprint("{cyan}Done.")

def get_text(question: str, default = None) -> str:
	result = questionary.text(question if default is None else f"{question} (Default: \"{default}\")").ask()

	if result is None:
		raise Exception("Cancelled")

	if default is not None and result == "":
		return default

	return result

def get_selection(question: str, options: Sequence[str]) -> str:
	result = questionary.select(question, options).ask()

	if result is None:
		raise Exception("Cancelled")

	return result

if __name__ == "__main__":
	main()