# Neo4j 数据加载：连接与三元组/子图写入
from typing import List, Dict, Any, Optional, Tuple

Triple = Tuple[str, str, str]


def _serialize_value(v: Any) -> Any:
    """将 py2neo Node/Relationship 转为可序列化 dict。"""
    if v is None:
        return None
    cls_name = type(v).__name__
    if cls_name == "Node":
        labels = list(v.labels) if hasattr(v, "labels") else []
        props = dict(v) if hasattr(v, "keys") else {}
        return {"_type": "Node", "labels": labels, "properties": props}
    if cls_name == "Relationship":
        rel_type = type(v).__name__ if hasattr(v, "__class__") else "REL"
        props = dict(v) if hasattr(v, "keys") else {}
        return {"_type": "Relationship", "type": rel_type, "properties": props}
    if isinstance(v, (list, tuple)):
        return [_serialize_value(x) for x in v]
    if isinstance(v, dict):
        return {k: _serialize_value(x) for k, x in v.items()}
    return v


class Neo4jLoader:
    """Neo4j 加载器：连接数据库，写入节点与关系。"""

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self._graph = None

    def connect(self) -> None:
        """建立 Neo4j 连接。"""
        try:
            from py2neo import Graph
            self._graph = Graph(self.uri, auth=(self.username, self.password))
        except Exception as e:
            raise RuntimeError(f"Neo4j 连接失败: {e}") from e

    def close(self) -> None:
        """关闭连接。"""
        self._graph = None

    def __enter__(self) -> "Neo4jLoader":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    @property
    def graph(self):
        """获取 py2neo Graph，未连接则先连接。"""
        if self._graph is None:
            self.connect()
        return self._graph

    def create_constraints_and_indexes(self, ontology: Any) -> None:
        """根据本体设计创建唯一约束与索引。"""
        labels = getattr(ontology, "get_entity_labels", lambda: [])()
        for label in labels:
            try:
                self.graph.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE").consume()
            except Exception:
                pass

    def load_triples(
        self,
        triples: List[Triple],
        head_label: Optional[str] = None,
        tail_label: Optional[str] = None,
        merge: bool = True,
    ) -> int:
        """批量写入三元组。"""
        count = 0
        for h, rel, t in triples:
            try:
                if merge:
                    self.graph.run(
                        "MERGE (a {name: $h}) MERGE (b {name: $t}) MERGE (a)-[r:" + rel + "]->(b)",
                        h=h, t=t
                    )
                else:
                    self.graph.run(
                        "CREATE (a {name: $h})-[:%s]->(b {name: $t})" % rel, h=h, t=t
                    )
                count += 1
            except Exception:
                continue
        return count

    def clear_graph(self) -> None:
        """清空图数据（慎用）。"""
        self.graph.run("MATCH (n) DETACH DELETE n").consume()

    def run_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行 Cypher 查询，返回可序列化的记录列表。"""
        params = parameters or {}
        cursor = self.graph.run(query, **params)
        out = []
        for record in cursor:
            row = {}
            for key in record.keys():
                row[key] = _serialize_value(record[key])
            out.append(row)
        return out
