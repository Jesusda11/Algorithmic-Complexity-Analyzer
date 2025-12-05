# tests/test_api.py
"""
Tests de integración para la API
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# =====================================
# TESTS DE HEALTH
# =====================================

def test_health_endpoint():
    """Test del endpoint de salud"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "uptime_seconds" in data


def test_root_redirect():
    """Test de redirección del root"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Redirect
    assert response.headers["location"] == "/docs"


# =====================================
# TESTS DE ANÁLISIS
# =====================================

def test_analyze_factorial():
    """Test análisis de factorial"""
    code = """
procedure Factorial(n)
begin
    if (n ≤ 1) then
    begin
        return 1
    end
    else
    begin
        return n * call Factorial(n - 1)
    end
end
    """
    
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "code": code,
            "enable_patterns": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "complexity" in data
    assert "procedures" in data
    
    # Verificar complejidad
    complexity = data["complexity"]
    assert "big_o" in complexity
    assert "omega" in complexity
    assert "theta" in complexity


def test_analyze_binary_search():
    """Test análisis de búsqueda binaria"""
    code = """
procedure BusquedaBinaria(A[], x, inicio, fin)
begin
    if (inicio > fin) then
    begin
        return -1
    end
    
    medio 🡨 (inicio + fin) div 2
    
    if (A[medio] = x) then
    begin
        return medio
    end
    else
    begin
        if (A[medio] > x) then
        begin
            call BusquedaBinaria(A, x, inicio, medio - 1)
        end
        else
        begin
            call BusquedaBinaria(A, x, medio + 1, fin)
        end
    end
end
    """
    
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "code": code,
            "enable_patterns": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    
    # Verificar que detectó Binary Search
    if "procedures" in data and "BusquedaBinaria" in data["procedures"]:
        proc = data["procedures"]["BusquedaBinaria"]
        assert proc["recursion_info"]["is_recursive"] is True
        
        # Debería ser O(log n)
        assert "log" in data["complexity"]["big_o"].lower()


def test_analyze_merge_sort():
    """Test análisis de merge sort"""
    code = """
procedure MergeSort(A[], inicio, fin)
begin
    if (inicio < fin) then
    begin
        medio 🡨 (inicio + fin) div 2
        call MergeSort(A, inicio, medio)
        call MergeSort(A, medio + 1, fin)
        call Merge(A, inicio, medio, fin)
    end
end
    """
    
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "code": code,
            "enable_patterns": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    
    # Debería detectar recursión
    if "procedures" in data and "MergeSort" in data["procedures"]:
        proc = data["procedures"]["MergeSort"]
        assert proc["recursion_info"]["is_recursive"] is True


# =====================================
# TESTS DE VALIDACIÓN
# =====================================

def test_empty_code():
    """Test con código vacío"""
    response = client.post(
        "/api/v1/analysis/analyze",
        json={"code": ""}
    )
    
    assert response.status_code == 422  # Validation error


def test_invalid_syntax():
    """Test con sintaxis inválida"""
    response = client.post(
        "/api/v1/analysis/analyze",
        json={"code": "begin without end"}
    )
    
    # Puede ser 400 o 500 dependiendo de dónde falle
    assert response.status_code in [400, 500]


def test_very_large_code():
    """Test con código muy grande"""
    large_code = "begin\n" + ("x 🡨 1\n" * 10000) + "end"
    
    response = client.post(
        "/api/v1/analysis/analyze",
        json={"code": large_code}
    )
    
    # Debería funcionar o dar error de tamaño
    assert response.status_code in [200, 400]


# =====================================
# TESTS DE OPCIONES
# =====================================

def test_include_ast():
    """Test con AST incluido"""
    code = "begin\nx 🡨 1\nend"
    
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "code": code,
            "include_ast": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "ast" in data
    assert data["ast"] is not None


def test_include_tokens():
    """Test con tokens incluidos"""
    code = "begin\nx 🡨 1\nend"
    
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "code": code,
            "include_tokens": True
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "tokens" in data
    assert data["tokens"] is not None
    assert len(data["tokens"]) > 0


def test_disable_patterns():
    """Test sin clasificación de patrones"""
    code = "procedure Test(n)\nbegin\nend"
    
    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "code": code,
            "enable_patterns": False
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # No debería tener clasificación de patrones
    if "procedures" in data and data["procedures"]:
        for proc in data["procedures"].values():
            assert "pattern" not in proc or proc["pattern"] is None


# =====================================
# TESTS DE BATCH
# =====================================

def test_batch_analyze():
    """Test de análisis batch"""
    codes = [
        "begin\nx 🡨 1\nend",
        "begin\nfor i 🡨 1 to n do\nbegin\nx 🡨 x + 1\nend\nend"
    ]
    
    response = client.post(
        "/api/v1/analysis/batch-analyze",
        json=codes
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 2
    assert len(data["results"]) == 2


def test_batch_too_many():
    """Test batch con demasiados códigos"""
    codes = ["begin\nend"] * 20  # Más de 10
    
    response = client.post(
        "/api/v1/analysis/batch-analyze",
        json=codes
    )
    
    assert response.status_code == 400


# =====================================
# TESTS DE CACHE
# =====================================

def test_cache_works():
    """Test que el cache funcione"""
    code = "begin\nx 🡨 1\nend"
    
    # Primera llamada
    response1 = client.post(
        "/api/v1/analysis/analyze",
        json={"code": code}
    )
    
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["metadata"]["from_cache"] is False
    
    # Segunda llamada (debería venir del cache)
    response2 = client.post(
        "/api/v1/analysis/analyze",
        json={"code": code}
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["metadata"]["from_cache"] is True
    
    # Limpiar cache
    response3 = client.delete("/api/v1/analysis/cache")
    assert response3.status_code == 200


# =====================================
# TESTS DE MÉTRICAS
# =====================================

def test_metrics_endpoint():
    """Test del endpoint de métricas"""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    data = response.json()
    
    assert "cpu_percent" in data
    assert "memory" in data
    assert "cache" in data


# =====================================
# RUN TESTS
# =====================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
