import os
import argparse
import logging
import subprocess
import tempfile
from pydantic import BaseModel
from openai import OpenAI
import diagrams
import importlib
import difflib
import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize exec_globals with the Diagram base class
exec_globals = {"Diagram": diagrams.Diagram}

system_prompt = f'''
You are an expert in the diagram tool Mingrammer and your job is to generate Mingrammer diagram code based on the user's descriptions.  
The response you generate should only contain the python code without anything else.  
It should not even be wrapped in ```python <generated_python_code> ```, instead it should just contain <generated_python_code>.


For example, below is a possible response because it just contains python code: \n

from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.onprem.queue import Kafka

with Diagram("AWS Lambda and Kafka", show=False):
    api_gateway = APIGateway("API Gateway")

    lambda1 = Lambda("Lambda 1")
    lambda2 = Lambda("Lambda 2")
    lambda3 = Lambda("Lambda 3")
    lambda4 = Lambda("Lambda 4")

    kafka_queue = Kafka("Kafka Queue")

    api_gateway >> lambda1 >> kafka_queue
    api_gateway >> lambda2 >> kafka_queue
    api_gateway >> lambda3 >> kafka_queue
    api_gateway >> lambda4 >> kafka_queue
    \n
Notice how in the above example, only python code is generated.

The following are some other examples of Mingrammer diagram generated code.\n
Example 1: Grouped Workers on AWS\n
from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Grouped Workers", show=False, direction="TB"):
    ELB("lb") >> [EC2("worker1"),
                  EC2("worker2"),
                  EC2("worker3"),
                  EC2("worker4"),
                  EC2("worker5")] >> RDS("events")
\n
Example 2:Clustered Web Services\n

from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.database import ElastiCache, RDS
from diagrams.aws.network import ELB
from diagrams.aws.network import Route53

with Diagram("Clustered Web Services", show=False):
    dns = Route53("dns")
    lb = ELB("lb")

    with Cluster("Services"):
        svc_group = [ECS("web1"),
                     ECS("web2"),
                     ECS("web3")]

    with Cluster("DB Cluster"):
        db_primary = RDS("userdb")
        db_primary - [RDS("userdb ro")]

    memcached = ElastiCache("memcached")

    dns >> lb >> svc_group
    svc_group >> db_primary
    svc_group >> memcached\n

Example 3: Event Processing on AWS\n

from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS, EKS, Lambda
from diagrams.aws.database import Redshift
from diagrams.aws.integration import SQS
from diagrams.aws.storage import S3

with Diagram("Event Processing", show=False):
    source = EKS("k8s source")

    with Cluster("Event Flows"):
        with Cluster("Event Workers"):
            workers = [ECS("worker1"),
                       ECS("worker2"),
                       ECS("worker3")]

        queue = SQS("event queue")

        with Cluster("Processing"):
            handlers = [Lambda("proc1"),
                        Lambda("proc2"),
                        Lambda("proc3")]

    store = S3("events store")
    dw = Redshift("analytics")

    source >> workers >> queue >> handlers
    handlers >> store
    handlers >> dw\n

Example 4: Message Collecting System on GCP\n

from diagrams import Cluster, Diagram
from diagrams.gcp.analytics import BigQuery, Dataflow, PubSub
from diagrams.gcp.compute import AppEngine, Functions
from diagrams.gcp.database import BigTable
from diagrams.gcp.iot import IotCore
from diagrams.gcp.storage import GCS

with Diagram("Message Collecting", show=False):
    pubsub = PubSub("pubsub")

    with Cluster("Source of Data"):
        [IotCore("core1"),
         IotCore("core2"),
         IotCore("core3")] >> pubsub

    with Cluster("Targets"):
        with Cluster("Data Flow"):
            flow = Dataflow("data flow")

        with Cluster("Data Lake"):
            flow >> [BigQuery("bq"),
                     GCS("storage")]

        with Cluster("Event Driven"):
            with Cluster("Processing"):
                flow >> AppEngine("engine") >> BigTable("bigtable")

            with Cluster("Serverless"):
                flow >> Functions("func") >> AppEngine("appengine")

    pubsub >> flow\n

Example 5: Exposed Pod with 3 Replicas on Kubernetes\n

from diagrams import Diagram
from diagrams.k8s.clusterconfig import HPA
from diagrams.k8s.compute import Deployment, Pod, ReplicaSet
from diagrams.k8s.network import Ingress, Service

with Diagram("Exposed Pod with 3 Replicas", show=False):
    net = Ingress("domain.com") >> Service("svc")
    net >> [Pod("pod1"),
            Pod("pod2"),
            Pod("pod3")] << ReplicaSet("rs") << Deployment("dp") << HPA("hpa")\n

Example 6: Stateful Architecture on Kubernetes \n

from diagrams import Cluster, Diagram
from diagrams.k8s.compute import Pod, StatefulSet
from diagrams.k8s.network import Service
from diagrams.k8s.storage import PV, PVC, StorageClass

with Diagram("Stateful Architecture", show=False):
    with Cluster("Apps"):
        svc = Service("svc")
        sts = StatefulSet("sts")

        apps = []
        for _ in range(3):
            pod = Pod("pod")
            pvc = PVC("pvc")
            pod - sts - pvc
            apps.append(svc >> pod >> pvc)

    apps << PV("pv") << StorageClass("sc")\n

Example 7: RabbitMQ Consumers with Custom Nodes\n

from urllib.request import urlretrieve

from diagrams import Cluster, Diagram
from diagrams.aws.database import Aurora
from diagrams.custom import Custom
from diagrams.k8s.compute import Pod

# Download an image to be used into a Custom Node class
rabbitmq_url = "https://jpadilla.github.io/rabbitmqapp/assets/img/icon.png"
rabbitmq_icon = "rabbitmq.png"
urlretrieve(rabbitmq_url, rabbitmq_icon)

with Diagram("Broker Consumers", show=False):
    with Cluster("Consumers"):
        consumers = [
            Pod("worker"),
            Pod("worker"),
            Pod("worker")]

    queue = Custom("Message queue", rabbitmq_icon)

    queue >> consumers >> Aurora("Database")

Also, to remind you of some correct import paths:\n
The import path for dynamoDB is 'from diagrams.aws.database import Dynamodb'\n
remember that this is case sensitive so 'from diagrams.aws.database import DynamoDB' will not work because 'DynamoDB' 
has incorrect casing.\n

Never use 'from diagrams.custom import Custom' because we do not have any images to actually use.
Never use ClusterRole as a context manager e.g.\n
with ClusterRole("TPservice"):
        k8s_cluster = Lambda("Kubernetes Cluster")\n

'''


class DiagramRequest(BaseModel):
    description: str


def populate_exec_globals_and_get_imports() -> str:
    """Populate exec_globals with Mingrammer diagram classes and return valid import statements."""
    import_statements = []
    diagrams_path = os.path.dirname(diagrams.__file__)

    for root, dirs, files in os.walk(diagrams_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                relative_path = os.path.relpath(os.path.join(root, file), diagrams_path)
                module_name = f"diagrams.{relative_path[:-3].replace(os.path.sep, '.')}"

                try:
                    module = importlib.import_module(module_name)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type):
                            exec_globals[attr_name] = attr
                            import_statements.append(f"from {module_name} import {attr_name}")
                except ImportError:
                    pass
    return "\n".join(import_statements)


correct_imports = populate_exec_globals_and_get_imports()


def identify_incorrect_imports(generated_code: str, correct_imports: list) -> dict:
    """Identify incorrect import statements in the generated code."""
    incorrect_imports = {}
    for line in generated_code.splitlines():
        if (line.startswith("from diagrams") or line.startswith("import diagrams")) and line not in [
            "from diagrams import Diagram",
            "from diagrams import Cluster, Diagram",
        ]:
            if line not in correct_imports:
                closest_matches = [
                    match for match in difflib.get_close_matches(line, correct_imports, n=10, cutoff=0.6)
                    if not match.split()[-1].startswith("_")
                ]
                if closest_matches:
                    incorrect_imports[line] = closest_matches
    return incorrect_imports


def generate_correction_prompt(generated_code: str, incorrect_imports: dict, original_prompt: str) -> str:
    """Generate a prompt to correct invalid imports."""
    incorrect_imports_text = "\n".join(
        f"- Incorrect: {incorrect} | Suggested: {suggested}"
        for incorrect, suggested in incorrect_imports.items()
    )
    return f"""
    You are an expert code debugger.  I will show you some python code that uses the Mingrammer diagramming tool
    That uses some incorrect imports that I want you to fix.  The original intention of the code was the following:\n
    {original_prompt}\n  Below is the code with the incorrect imports: \n
    {generated_code}\n
    The incorrect import lines and some possible suggestions for correct imports is below.\n
    {incorrect_imports_text}\n
    Please replace only the incorrect import lines with the suggested imports. Keep the rest of the code unchanged.
    The response you generate should only contain the python code without anything else.  
    It should not even be wrapped in ```python <generated_python_code> ```, instead it should just contain <generated_python_code>.
    """


def execute_mingrammer_code(code: str) -> str:
    """Execute the generated Mingrammer code and return the diagram image path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_script:
        script_path = tmp_script.name
        tmp_script.write(code.encode())
        tmp_script.flush()

        try:
            subprocess.run(["python3", script_path], check=True, cwd=os.getcwd())
            output_path = get_latest_png_file()
            logging.info(f"Diagram successfully generated: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logging.error(f"Execution failed: {e}")
            raise RuntimeError("Failed to execute the generated Mingrammer code.")


def get_latest_png_file(directory="."):
    """Get the most recently created PNG file in the specified directory."""
    list_of_files = glob.glob(f"{directory}/*.png")
    if not list_of_files:
        raise FileNotFoundError("No PNG files found.")
    return max(list_of_files, key=os.path.getctime)


def main():
    parser = argparse.ArgumentParser(description="Translate natural language descriptions into diagrams.")
    parser.add_argument("description", type=str, help="The description of the diagram to generate.")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output path for the generated diagram (default: current directory).",
    )
    args = parser.parse_args()

    # OpenAI configuration
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"Generate Mingrammer diagrams code for the following description:\n\n{args.description}\n\nCode:"
    logging.info("Sending request to OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
        max_tokens=1084,
        temperature=0.5,
    )

    mingrammer_code = response.choices[0].message.content
    logging.info(f"Generated code:\n{mingrammer_code}")

    correct_imports_list = correct_imports.splitlines()
    incorrect_imports = identify_incorrect_imports(mingrammer_code, correct_imports_list)
    logging.info(f"Found the following incorrect inputs:\{incorrect_imports}")
    if incorrect_imports:
        correction_prompt = generate_correction_prompt(mingrammer_code, incorrect_imports, args.description)
        logging.info(f"Correction prompt:\n {correction_prompt}")
        logging.info(f"Sending correction request to OpenAI...")
        correction_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": correction_prompt}],
            max_tokens=1084,
            temperature=0.3,
        )
        mingrammer_code = correction_response.choices[0].message.content
        logging.info(f"Corrected code:\n{mingrammer_code}")

    try:
        output_path = execute_mingrammer_code(mingrammer_code)
        if args.output:
            os.rename(output_path, args.output)
            output_path = args.output
        logging.info(f"Diagram saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to generate diagram: {e}")
        exit(1)


if __name__ == "__main__":
    main()
