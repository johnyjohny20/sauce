import pafy
import billboard
from pytube import Playlist
import youtube_dl
import asyncio
import discord
from discord.ext import commands
purple = 0x843cdd
yt='https://img.icons8.com/external-those-icons-lineal-color-those-icons/24/000000/external-youtube-applications-windows-those-icons-lineal-color-those-icons.png'
class Sound(commands.Cog):
    def __init__(self, bot):
        self.bot = bot 
        self.song_queue = {}
        self.song_titles ={}
        self.song_time = {}
        

        self.setup()

    def setup(self):
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []
            self.song_titles[guild.id] =[]
            self.song_time[guild.id] = []

    async def check_queue(self, ctx):
            await self.play_song(ctx, self.song_queue[ctx.guild.id][0], self.song_time[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)
            self.song_titles[ctx.guild.id].pop(0)
            self.song_time[ctx.guild.id].pop(0)

    async def search_song(self, amount, song, get_url=False):
        info = await self.bot.loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL({"format" : "bestaudio", "quiet" : True}).extract_info(f"ytsearch{amount}:{song}", download=False, ie_key="YoutubeSearch"))
        if len(info["entries"]) == 0: return None

        return [entry["webpage_url"] for entry in info["entries"]] if get_url else info
    async def producer(self, ctx, song):
        music = pafy.new(song)
        def convert_timer(seconds):
                a = (seconds//3600)
                b=((seconds%3600)//60)
                c=((seconds%3600)%60)
                if a == 0:
                    return '{:02d}:{:02d}'.format(b, c)
                else:
                    return '{:02d}:{:02d}:{:02d}'.format(a, b, c)
        if ctx.voice_client.source is  not None:
            queue_len = len(self.song_queue[ctx.guild.id])
            if queue_len  < 100:
                self.song_titles[ctx.guild.id].append(music.title)
                self.song_time[ctx.guild.id].append(convert_timer(music.length))
                self.song_queue[ctx.guild.id].append(song)
                return None
           
            else:
                embed2 = discord.Embed(title='Queue overload please wait to finish current song', color=discord.Colour.red())
                return await ctx.send(embed = embed2)
        await self.play_song(ctx, song,convert_timer(music.length))

    async def play_song(self, ctx, song, time):   
        music = pafy.new(song)
        url = pafy.new(song).getbestaudio().url
        ctx.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url)), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        ctx.voice_client.source.volume = 0.8
        def next_song():
            try:
                 title = self.song_titles[ctx.guild.id][1]
                 return title
            except Exception as e:
                print(e)
                return 'No queue yet...'
        embed2 = discord.Embed(title=music.title, url=song,color=0x843cdd)
        embed2.set_author(name='Now Playing: ', icon_url=yt)
        embed2.add_field(name=':clock4: Duration', value=time)
        embed2.set_thumbnail(url=music.bigthumbhd)
        embed2.add_field(name=':musical_note: Next Song: ' ,value=next_song(), inline=True)
        embed2.set_footer(text=f'requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
        
        await ctx.send(embed=embed2)
       
    
    @commands.command()
    async def leave(self, ctx):
      if ctx.voice_client is not None:
            await ctx.send(':door:  i leave your channel and clear queue ')
                     
            self.song_queue[ctx.guild.id].clear() 
            self.song_titles[ctx.guild.id].clear() 
            self.song_time[ctx.guild.id].clear() 
            return await ctx.voice_client.disconnect() 

    @commands.command(name='p')
    async def play(self, ctx, *, song=None):
        queue_len = len(self.song_queue[ctx.guild.id])
        if ctx.author.voice is None:
            await ctx.send('you are not in voice channel')
       
        if song is None:
            return await ctx.send("missing song argument.")

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
       

        # handle song where song isn't URL
        if ('https://www.youtube.com/playlist' in song):
            embed2=discord.Embed(title=':trumpet: Playlist added to the queue! :trumpet:',color=purple)
            await ctx.send(embed=embed2)
            playlist = Playlist(song)
            for video in playlist:
                await self.producer(ctx, video)
        elif ('youtube.com/watch? 'in song ):
            audio = pafy.new(song)
            embed2 = discord.Embed(title= audio.title, url=song, color=purple)
            embed2.set_author(name=f'Positioned at {queue_len + 1}', icon_url=yt)
            embed2.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed2)
            await self.producer(ctx, song)
           
        elif not ("youtube.com/watch?" in song ):
            await ctx.send("fetching results...")
            music = f'{song}  lyrics'
            result = await self.search_song(2,  music, get_url=True)
            print(result)
            src = result[1]
            audio = pafy.new(src)
            embed2 = discord.Embed(title= audio.title, url=src, color=purple)
            embed2.set_author(name=f'Positoned at {queue_len +1}', icon_url=yt)
            embed2.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed2)
            if result is None:
                return await ctx.send("Sorry, I could not find the given song, try using my search command.")


            await self.producer(ctx, src)
        
      

    @commands.command(name='m')
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send("You forgot to include a song to search for.")

        await ctx.send("Searching for song, this may take a few seconds.")

        info = await self.search_song(5, song)

        embed = discord.Embed(title=f"Results for '{song}':", description="*You can use these URL's to play an exact song if the one you want isn't the first result.*\n", colour=discord.Colour.red())
        
        amount = 0
        for entry in info["entries"]:
            embed.description += f"[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1

        embed.set_footer(text=f"Displaying the first {amount} results.")
        await ctx.send(embed=embed)

    @commands.command(name='q')
    async def queue(self, ctx): # display the current guilds queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are currently no songs in the queue.")
        embed = discord.Embed(title="Song Queue", description="", colour=discord.Colour.blurple())
        i = 1
        for title, duration in zip(self.song_titles[ctx.guild.id], self.song_time[ctx.guild.id]):
           
            embed.description += f"{i}) {title} `{duration}`\n"
            i += 1

        embed.set_footer(text="tip: you can use #m to search tracks without playing")
        await ctx.send(embed=embed)
    @commands.command()
    async def billboard(self, ctx,type: int=None):
        if ctx.author.voice is None:
            await ctx.send('you are not in voice channel')

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        vc = ctx.voice_client
        bb =[]
        if type is None:
            chart = billboard.ChartData('hot-100')
            songf = chart[0]
            # displaying the first item in the chart
            embed2 = discord.Embed(color=discord.Colour.red())
            embed2.set_author(name='Billboard Hot-100', icon_url='https://static.billboard.com/files/2019/07/billboard-logo-b-20-billboard-1548-1092x722-1598619661-compressed.jpg')
            embed2.add_field(name=':trophy: Number 1 in the chart', value=f'{songf.title}, - {songf.artist}')
            embed2.set_thumbnail(url='https://i.scdn.co/image/ab67706c0000bebb3bd5501a335b265807df34db')
            await ctx.send(embed=embed2)
             
            for song in chart: # iterating every song in the list.
                song = (f'{song.artist} {song.title}, lyrics')
                bb.append(song)
        if type:
            #fuck i hate programming :(
            chart = billboard.ChartData('hot-100-songs', year=type)
            songf = chart[0]
            # displaying the first item in the chart
            embed2 = discord.Embed(color=discord.Colour.red())
            embed2.set_author(name=f'Billboard Year End Hot-100 songs of {type}', icon_url='https://static.billboard.com/files/2019/07/billboard-logo-b-20-billboard-1548-1092x722-1598619661-compressed.jpg')
            embed2.add_field(name=':trophy: Number 1 in the chart', value=f'{songf.title} - {songf.artist}')
            embed2.set_thumbnail(url='https://i.scdn.co/image/ab67706c0000bebb3bd5501a335b265807df34db')
            await ctx.send(embed=embed2)
             
            for song in chart: # iterating every song in the list.
                song = (f'{song.artist} {song.title}, lyrics')
                bb.append(song)
 
        for song in bb:
            result = await self.search_song(2, song, get_url=True)
            song = result[1]
            await self.producer(ctx, song)
        if vc.is_playing():
            await ctx.send(':musical_note: added to queue')
        asyncio.sleep(5)
        await self.check_queue(ctx)

    @commands.command()
    async def skip(self, ctx, amount: int=None):
        if ctx.voice_client is None:
            return await ctx.send("I am not playing any song.")

        if ctx.author.voice is None:
            return await ctx.send("You are not connected to any voice channel.")

        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
      
            return await ctx.send("No songs in queue yet.")
        skip=True

        try:
            if amount is None:
                ctx.voice_client.stop()
                await self.check_queue(ctx)
            if amount is not None:
                amount -= 1
                del self.song_queue[ctx.guild.id][0:amount]
                del self.song_titles[ctx.guild.id][0:amount]
                del self.song_time[ctx.guild.id][0:amount]
                
                ctx.voice_client.stop()
                await self.check_queue(ctx)
        except IndexError as e:
            print(e)
            await ctx.send(':warning: youre trying to remove what is none, try getting queue before overskip.')
    @commands.command()
    async def remove(self, ctx, all=None, amount: int=None):
        try:
            if all == 'all':
                self.song_queue[ctx.guild.id].clear()
                self.song_titles[ctx.guild.id].clear()
                self.song_time[ctx.guild.id].clear()
                await ctx.send(':broom: succesfully remove all queue')

            if amount is not None:
                amount -= 1
                self.song_queue[ctx.guild.id].pop(amount)
                self.song_titles[ctx.guild.id].pop(amount)
                self.song_time[ctx.guild.id].pop(amount)
                await ctx.send('succefully remove song!')
                await self.queue(ctx)
            if amount is None and all is None:
                await ctx.send('please remove number based on queue, cant find? try **$q**')
        except Exception as e:
            print(e)
            await ctx.send('error, ')


    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("I am already paused.")

        ctx.voice_client.pause()
        await ctx.send("The current song has been paused.")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not connected to a voice channel.")

        if not ctx.voice_client.is_paused():
            return await ctx.send("I am already playing a song.")
        
        ctx.voice_client.resume()
        await ctx.send("The current song has been resumed.") 
