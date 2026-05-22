from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import httpx
import os
from collections import defaultdict

# dino hidden reference
app = FastAPI(title="Pokemon Recommendation Engine")

pokeapi_base_url = os.getenv("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2")
redis_url = os.getenv("REDIS_URL", "redis://cache-service:6379")

class Team(BaseModel):
    pokemon_ids: List[int]

class RecommendationRequest(BaseModel):
    team: Team
    count: int = 1

# Type effectiveness matrix
type_effectiveness = {
    "normal": {"roche": 0.5, "spectre": 0, "acier": 0.5},
    "feu": {"feu": 0.5, "eau": 0.5, "plante": 2, "glace": 2, "insecte": 2, "roche": 0.5, "dragon": 0.5, "acier": 2},
    "eau": {"feu": 2, "eau": 0.5, "plante": 0.5, "sol": 2, "roche": 2, "dragon": 0.5},
    "plante": {"feu": 0.5, "eau": 2, "plante": 0.5, "poison": 0.5, "sol": 2, "vol": 0.5, "insecte": 0.5, "roche": 2, "dragon": 0.5, "acier": 0.5},
    "electrique": {"eau": 2, "electrique": 0.5, "plante": 0.5, "sol": 0, "vol": 2, "dragon": 0.5},
    "glace": {"feu": 0.5, "eau": 0.5, "plante": 2, "glace": 0.5, "sol": 2, "vol": 2, "dragon": 2, "acier": 0.5},
    "combat": {"normal": 2, "glace": 2, "poison": 0.5, "vol": 0.5, "psy": 0.5, "insecte": 0.5, "roche": 2, "spectre": 0, "tenebres": 2, "acier": 2, "fee": 0.5},
    "poison": {"plante": 2, "poison": 0.5, "sol": 0.5, "roche": 0.5, "spectre": 0.5, "acier": 0, "fee": 2},
    "sol": {"feu": 2, "electrique": 2, "plante": 0.5, "poison": 2, "vol": 0, "insecte": 0.5, "roche": 2, "acier": 2},
    "vol": {"electrique": 0.5, "plante": 2, "combat": 2, "insecte": 2, "roche": 0.5, "acier": 0.5},
    "psy": {"combat": 2, "poison": 2, "psy": 0.5, "tenebres": 0, "acier": 0.5},
    "insecte": {"feu": 0.5, "plante": 2, "combat": 0.5, "poison": 0.5, "vol": 0.5, "psy": 2, "spectre": 0.5, "tenebres": 2, "acier": 0.5, "fee": 0.5},
    "roche": {"feu": 2, "glace": 2, "combat": 0.5, "sol": 0.5, "vol": 2, "insecte": 2, "acier": 0.5},
    "spectre": {"normal": 0, "psy": 2, "spectre": 2, "tenebres": 0.5},
    "dragon": {"dragon": 2, "acier": 0.5, "fee": 0},
    "tenebres": {"combat": 0.5, "psy": 2, "spectre": 2, "tenebres": 0.5, "fee": 0.5},
    "acier": {"feu": 0.5, "eau": 0.5, "electrique": 0.5, "glace": 2, "roche": 2, "acier": 0.5, "fee": 2},
    "fee": {"feu": 0.5, "combat": 2, "poison": 0.5, "dragon": 2, "tenebres": 2, "acier": 0.5}
}

def get_type_coverage(team_types: List[str]) -> dict:
    """Calculate type coverage for a team"""
    coverage = defaultdict(float)
    
    for type_name in team_types:
        if type_name in type_effectiveness:
            for defender, multiplier in type_effectiveness[type_name].items():
                coverage[defender] = max(coverage[defender], multiplier)
    
    return coverage

def get_type_weaknesses(team_types: List[str]) -> dict:
    """Calculate type weaknesses for a team"""
    weaknesses = defaultdict(list)
    
    for type_name in team_types:
        for attacker, effectiveness in type_effectiveness.items():
            if type_name in effectiveness:
                multiplier = effectiveness[type_name]
                if multiplier > 1.0:
                    weaknesses[attacker].append(multiplier)
    
    return weaknesses

async def get_pokemon_types(pokemon_id: int) -> List[str]:
    """Fetch pokemon types from PokeAPI"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{pokeapi_base_url}/pokemon/{pokemon_id}")
        if response.status_code != 200:
            return []
        data = response.json()
        types = [t["type"]["name"] for t in data["types"]]
        return types

def calculate_team_score(team_types: List[str], candidate_types: List[str]) -> float:
    """
    Calculate how well a candidate complements a team
    Higher score = better complement
    """
    # Get current team coverage and weaknesses
    current_coverage = get_type_coverage(team_types)
    current_weaknesses = get_type_weaknesses(team_types)
    
    # Get candidate coverage
    candidate_coverage = get_type_coverage(candidate_types)
    
    score = 0.0
    
    # Points for covering team weaknesses
    for weak_type, multipliers in current_weaknesses.items():
        if weak_type in candidate_coverage and candidate_coverage[weak_type] >= 2.0:
            score += 10.0 * len(multipliers)
    
    # Points for adding new offensive coverage
    for defender, multiplier in candidate_coverage.items():
        if defender not in current_coverage or current_coverage[defender] < multiplier:
            score += multiplier * 5.0
    
    # Penalty for type redundancy
    type_counts = defaultdict(int)
    for t in team_types:
        type_counts[t] += 1
    
    for t in candidate_types:
        if type_counts[t] > 0:
            score -= 5.0 * type_counts[t]
    
    return score

@app.post("/recommend")
async def recommend_pokemon(request: RecommendationRequest):
    """
    Recommend pokemon to complete a team
    Uses type coverage analysis and weakness compensation
    """
    if len(request.team.pokemon_ids) >= 6:
        raise HTTPException(status_code=400, detail="Team is already full")
    
    # Get types of current team
    team_types = []
    for pokemon_id in request.team.pokemon_ids:
        types = await get_pokemon_types(pokemon_id)
        team_types.extend(types)
    
    # Score all pokemon (simplified: checking first 151)
    recommendations = []
    
    for candidate_id in range(1, 152):
        if candidate_id in request.team.pokemon_ids:
            continue
        
        candidate_types = await get_pokemon_types(candidate_id)
        if not candidate_types:
            continue
        
        score = calculate_team_score(team_types, candidate_types)
        recommendations.append({
            "pokemon_id": candidate_id,
            "score": score,
            "types": candidate_types
        })
    
    # Sort by score and return top N
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "recommendations": recommendations[:request.count],
        "team_analysis": {
            "coverage": dict(get_type_coverage(team_types)),
            "weaknesses": dict(get_type_weaknesses(team_types))
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
