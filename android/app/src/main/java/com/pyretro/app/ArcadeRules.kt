package com.pyretro.app
import org.json.JSONObject
object ArcadeRules {
    fun parse(data:JSONObject):JSONObject {
        require(data.optInt("schema")==1);val parents=data.getJSONObject("parents");require(parents.length()<=100000);val safe=Regex("[A-Za-z0-9_-]+")
        for(name in parents.keys())require(safe.matches(name) && (parents.getString(name).isEmpty() || safe.matches(parents.getString(name))))
        return parents
    }
    fun dependents(entry:String,inventory:Collection<String>,parents:JSONObject?):List<String> {
        fun stem(name:String)=name.substringAfterLast('/').substringBeforeLast('.')
        val others=inventory.filter { it!=entry && it.substringAfterLast('.').lowercase() in setOf("zip","7z") }
        require(others.all { parents?.has(stem(it))==true }) { "Índice de dependências de Arcade indisponível/incompleto. Sincronize a Biblioteca antes de remover." }
        return others.filter { name -> var current=parents?.optString(stem(name)).orEmpty();val seen=mutableSetOf<String>();var found=false
            while(current.isNotBlank() && current !in seen && seen.size<8) { if(current==stem(entry))found=true;seen.add(current);current=parents?.optString(current).orEmpty() };found
        }.sorted()
    }
}
