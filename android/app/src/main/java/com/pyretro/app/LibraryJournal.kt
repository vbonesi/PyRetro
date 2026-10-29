package com.pyretro.app

import org.json.JSONArray
import org.json.JSONObject

data class JournalRow(val localSeq:Long,val origin:String,val event:JSONObject)
interface JournalDb {
    fun <T> transaction(action:()->T):T
    fun library():JSONObject
    fun saveLibrary(value:JSONObject)
    fun meta(key:String):Any?
    fun putMeta(key:String,value:Any)
    fun append(event:JSONObject,origin:String):Long
    fun rows(since:Long=0,origin:String?=null):List<JournalRow>
}
data class JournalMerge(val library:JSONObject,val applied:Int,val state:JSONObject)

/** Espelho de core/journal_rules.py e library_journal.diff; sem dependência Android. */
object JournalRules {
    val ops=setOf("add","remove","set","unset","meta","session")
    fun copy(value:JSONObject)=JSONObject(value.toString())
    fun same(a:Any?,b:Any?):Boolean {
        if(a==null || a==JSONObject.NULL)return b==null || b==JSONObject.NULL
        if(b==null || b==JSONObject.NULL)return false
        if(a is Number && b is Number)return a.toDouble()==b.toDouble()
        if(a is JSONObject && b is JSONObject)return a.keys().asSequence().toSet()==b.keys().asSequence().toSet() && a.keys().asSequence().all { same(a.opt(it),b.opt(it)) }
        if(a is JSONArray && b is JSONArray)return a.length()==b.length() && (0 until a.length()).all { same(a.opt(it),b.opt(it)) }
        return a==b
    }
    fun games(library:JSONObject):LinkedHashMap<String,JSONObject> {
        val rows=library.optJSONArray("games") ?: JSONArray();val out=linkedMapOf<String,JSONObject>()
        for(i in 0 until rows.length()) { val g=rows.getJSONObject(i);val id=g.getString("id");require(id.isNotBlank() && id !in out) { "Biblioteca com identidade inválida/duplicada." };out[id]=g }
        return out
    }
    fun clock(now:Double,seen:Double)=maxOf(now,Math.nextUp(seen))
    fun diff(before:JSONObject,after:JSONObject):List<JSONObject> {
        val old=games(before);val new=games(after);val changes=mutableListOf<JSONObject>()
        for((id,g) in new) {
            val previous=old[id]
            if(previous==null) { changes.add(JSONObject().put("op","add").put("id",id).put("value",copy(g)));continue }
            for(field in (previous.keys().asSequence().toSet()+g.keys().asSequence().toSet()).sorted()) {
                if(field=="_play_sessions") {
                    val sessions=g.optJSONObject(field) ?: JSONObject();val known=previous.optJSONObject(field) ?: JSONObject()
                    for(event in sessions.keys())if(!known.has(event))changes.add(JSONObject().put("op","session").put("id",id).put("value",JSONObject().put("event",event).put("seconds",sessions.getLong(event))))
                } else if(previous.has(field)!=g.has(field) || !same(previous.opt(field),g.opt(field))) {
                    val c=JSONObject().put("op",if(g.has(field))"set" else "unset").put("id",id).put("field",field)
                    if(g.has(field))c.put("value",g.opt(field));changes.add(c)
                }
            }
        }
        for(id in old.keys-new.keys)changes.add(JSONObject().put("op","remove").put("id",id))
        for(field in ((before.keys().asSequence().toSet()+after.keys().asSequence().toSet())-"games").sorted())
            if(!same(before.opt(field),after.opt(field)))changes.add(JSONObject().put("op","meta").put("field",field).put("value",after.opt(field) ?: JSONObject.NULL))
        return changes
    }
    fun valid(c:JSONObject):Boolean {
        val op=c.optString("op");if(op !in ops)return false
        if(op!="meta" && (c.opt("id") !is String || c.optString("id").length !in 1..512))return false
        if(op in setOf("set","unset","meta") && (c.opt("field") !is String || c.optString("field").isBlank() || c.optString("field") in setOf("id","games","_play_sessions")))return false
        if(op=="add" && c.optJSONObject("value")?.optString("id")!=c.optString("id"))return false
        if(op=="session") {
            val v=c.optJSONObject("value") ?: return false;val seconds=v.opt("seconds") as? Number ?: return false
            return v.opt("event") is String && v.optString("event").length in 1..256 && seconds.toDouble()==seconds.toLong().toDouble() && seconds.toLong() in 1..365L*86400
        }
        return true
    }
    private fun key(id:String?,field:String?)=JSONArray().put(id ?: JSONObject.NULL).put(field ?: JSONObject.NULL).toString()
    private fun compare(a:JSONArray,b:JSONArray):Int = a.getDouble(0).compareTo(b.getDouble(0)).takeIf { it!=0 }
        ?: a.getString(1).compareTo(b.getString(1)).takeIf { it!=0 } ?: a.getLong(2).compareTo(b.getLong(2))
    fun merge(base:JSONObject,changes:List<JSONObject>,previous:JSONObject=JSONObject(),replayPending:Boolean=true):JournalMerge {
        val library=copy(base);val state=copy(previous);val versions=state.optJSONObject("versions") ?: JSONObject().also { state.put("versions",it) }
        val deleted=state.optJSONObject("deleted") ?: JSONObject().also { state.put("deleted",it) };val games=games(library)
        val pending=state.optJSONArray("pending") ?: JSONArray();val waiting=mutableListOf<JSONObject>();val incoming=mutableListOf<JSONObject>()
        for(i in 0 until pending.length())if(replayPending)incoming.add(pending.getJSONObject(i)) else waiting.add(pending.getJSONObject(i))
        incoming.addAll(changes);var applied=0
        fun version(id:String?,field:String?)=versions.optJSONArray(key(id,field)) ?: JSONArray().put(-1).put("").put(0)
        for(c in incoming) {
            if(!valid(c))continue
            val at=(c.opt("at") as? Number)?.toDouble() ?: continue;val seq=(c.opt("seq") as? Number)?.toLong() ?: continue
            if(!at.isFinite() || at<0 || seq<=0)continue
            val stamp=JSONArray().put(at).put(c.getString("device")).put(seq);val op=c.getString("op")
            val id=if(c.has("id"))c.getString("id") else null;val field=if(c.has("field"))c.getString("field") else null;val broad=version(id,null)
            when(op) {
                "meta" -> { if(compare(stamp,version(null,field))<=0)continue;library.put(field!!,c.opt("value") ?: JSONObject.NULL);versions.put(key(null,field),stamp) }
                "remove" -> {
                    if(versions.keys().asSequence().any { JSONArray(it).opt(0)==id && compare(stamp,versions.getJSONArray(it))<=0 })continue
                    games.remove(id)?.let { deleted.put(id!!,it) };versions.put(key(id,null),stamp)
                }
                "add" -> {
                    val value=c.getJSONObject("value")
                    if(compare(stamp,broad)<=0) { if(!deleted.has(id!!))deleted.put(id,copy(value));continue }
                    val game=games.getOrPut(id!!) { JSONObject().put("id",id) }
                    for(name in value.keys()) {
                        if(name=="_play_sessions") { val sessions=game.optJSONObject(name) ?: JSONObject().also { game.put(name,it) };val extra=value.getJSONObject(name);for(event in extra.keys())sessions.put(event,extra.get(event)) }
                        else if(compare(stamp,broad)>0 && compare(stamp,version(id,name))>0) { game.put(name,value.get(name));versions.put(key(id,name),stamp) }
                    }
                    deleted.remove(id)
                }
                else -> {
                    if(op!="session" && (compare(stamp,broad)<=0 || compare(stamp,version(id,field))<=0))continue
                    if(id !in games) {
                        if(compare(stamp,broad)<=0 || !deleted.has(id!!)) { if(compare(stamp,broad)>0)waiting.add(copy(c));continue }
                        games[id]=copy(deleted.getJSONObject(id))
                    }
                    val game=games.getValue(id!!)
                    when(op) {
                        "session" -> {
                            val v=c.getJSONObject("value");val event=v.getString("event");val seconds=v.getLong("seconds")
                            val sessions=game.optJSONObject("_play_sessions") ?: JSONObject().also { game.put("_play_sessions",it) }
                            if(sessions.has(event)) { require(sessions.getLong(event)==seconds) { "Sessão com conteúdo divergente; diário preservado." };continue }
                            sessions.put(event,seconds);versions.put(key(id,"_play_sessions:$event"),stamp)
                        }
                        "set" -> { game.put(field!!,c.opt("value") ?: JSONObject.NULL);versions.put(key(id,field),stamp) }
                        "unset" -> { game.remove(field);versions.put(key(id,field),stamp) }
                    }
                }
            }
            applied++
        }
        library.put("games",JSONArray(games.values.toList()))
        val unique=waiting.associateBy { it.getString("device")+":"+it.getLong("seq") }.values;require(unique.size<=10000)
        val ready=if(replayPending)unique.filter { it.optString("id") in games || deleted.has(it.optString("id")) } else emptyList()
        state.put("pending",JSONArray(if(replayPending)unique.filter { it !in ready } else unique.toList()))
        if(ready.isNotEmpty()) { val next=merge(library,ready,state);return next.copy(applied=applied+next.applied) }
        return JournalMerge(library,applied,state)
    }
}

/** Diário transacional: recibos e relógio só avançam depois da gravação local. */
class LibraryJournal(private val db:JournalDb,val device:String,private val now:()->Double={ System.currentTimeMillis()/1000.0 }) {
    init { require(Regex("[A-Za-z0-9][A-Za-z0-9_.-]{0,127}").matches(device)) }
    fun library()=db.library()
    fun pending()=db.rows((db.meta("published") as? Number)?.toLong() ?: 0,"local").size
    fun record(after:JSONObject):Int=db.transaction {
        val before=db.library();val changes=JournalRules.diff(before,after);if(changes.isEmpty())return@transaction 0
        val at=JournalRules.clock(now(),(db.meta("last_at") as? Number)?.toDouble() ?: 0.0)
        for(c in changes) { c.put("at",at).put("device",device);val seq=db.append(c,"local");c.put("seq",seq) }
        val state=JournalRules.merge(before,changes,db.meta("state") as? JSONObject ?: JSONObject(),replayPending=false).state
        db.saveLibrary(after);db.putMeta("state",state);db.putMeta("last_at",at);changes.size
    }
    fun seed(library:JSONObject)=db.transaction { if(db.meta("seeded")!=true) { db.saveLibrary(library);db.putMeta("seeded",true) } }
    fun bootstrap(snapshot:JSONObject,checkpoint:JSONObject)=db.transaction {
        if(db.meta("cloud_loaded")==true)return@transaction
        val locals=db.rows(origin="local").map { it.event };val merged=JournalRules.merge(snapshot,locals,checkpoint.optJSONObject("state") ?: JSONObject())
        db.saveLibrary(merged.library);db.putMeta("state",merged.state)
        db.putMeta("last_at",maxOf((db.meta("last_at") as? Number)?.toDouble() ?: 0.0,checkpoint.optDouble("last_at",0.0)))
        checkpoint.optJSONObject("cursors")?.let { cursors -> for(who in cursors.keys())if(who!=device)db.putMeta("remote:$who",cursors.getLong(who)) }
        db.putMeta("seeded",true);db.putMeta("cloud_loaded",true)
    }
    fun publish(store:CloudStorage):Int {
        var sent=0
        while(true) {
            val done=(db.meta("published") as? Number)?.toLong() ?: 0
            val rows=db.rows(done,"local").take(2000);if(rows.isEmpty())return sent
            val first=rows.first().localSeq;val last=rows.last().localSeq
            val segment=JSONObject().put("device",device).put("from",first).put("to",last).put("changes",JSONArray(rows.map { it.event }))
            val path="journal/$device/${"%012d".format(java.util.Locale.ROOT,first)}-${"%012d".format(java.util.Locale.ROOT,last)}.json"
            try { store.put(path,segment.toString().toByteArray()) }
            catch(_:CloudExists) { require(JournalRules.same(JSONObject(String(store.get(path),Charsets.UTF_8)),segment)) { "Segmento remoto diverge; fila preservada." } }
            db.transaction { db.putMeta("published",maxOf(last,(db.meta("published") as? Number)?.toLong() ?: 0)) };sent+=rows.size
        }
    }
    fun pull(store:CloudStorage):Int {
        var applied=0
        val paths=store.list("journal").map { it.path }.filter { Regex("journal/[A-Za-z0-9][A-Za-z0-9_.-]{0,127}/[0-9]+-[0-9]+\\.json").matches(it) }.sorted()
        for(path in paths) {
            val who=path.split('/')[1];if(who==device)continue
            val segment=JSONObject(String(store.get(path),Charsets.UTF_8));val first=segment.getLong("from");val last=segment.getLong("to")
            require(segment.getString("device")==who && first>0 && last>=first) { "Segmento inválido; recibo preservado." }
            val rows=segment.getJSONArray("changes");require(rows.length()<=2000);val events=mutableListOf<JSONObject>();val sequences=mutableSetOf<Long>()
            for(i in 0 until rows.length()) {
                val c=JournalRules.copy(rows.getJSONObject(i));if(c.optString("op") !in JournalRules.ops)continue
                val at=(c.opt("at") as? Number)?.toDouble();val seq=(c.opt("seq") as? Number)?.toLong()
                require(JournalRules.valid(c) && at!=null && at.isFinite() && at>=0 && seq!=null && seq in first..last && sequences.add(seq)) { "Mudança inválida; recibo preservado." }
                events.add(c.put("device",who))
            }
            db.transaction {
                val seen=(db.meta("remote:$who") as? Number)?.toLong() ?: 0;if(last<=seen)return@transaction
                val fresh=events.filter { it.getLong("seq")>seen };val merged=JournalRules.merge(db.library(),fresh,db.meta("state") as? JSONObject ?: JSONObject())
                db.saveLibrary(merged.library);db.putMeta("state",merged.state)
                for(c in fresh)db.append(c,"remote")
                db.putMeta("last_at",maxOf((db.meta("last_at") as? Number)?.toDouble() ?: 0.0,fresh.maxOfOrNull { it.getDouble("at") } ?: 0.0))
                db.putMeta("remote:$who",last);applied+=merged.applied
            }
        }
        db.transaction { val merged=JournalRules.merge(db.library(),emptyList(),db.meta("state") as? JSONObject ?: JSONObject());db.saveLibrary(merged.library);db.putMeta("state",merged.state);applied+=merged.applied }
        return applied
    }
}
