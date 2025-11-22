def parse_pseudocode(text):
    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]

    structure = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detectar FOR mínimo
        if line.startswith("para") and "hasta" in line:
            # Ejemplo: "para i = 1 hasta n hacer"
            parts = line.split()
            iterations = parts[parts.index("hasta") + 1]  # obtiene "n"

            body = []
            i += 1

            # Leer hasta fin del for
            while i < len(lines) and not lines[i].startswith("finpara"):
                body.append({"type": "operation", "cost": 1})
                i += 1

            structure.append({
                "type": "for",
                "iterations": iterations,
                "body": body
            })

        i += 1

    return structure
