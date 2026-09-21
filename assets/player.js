/* Leitor dos vídeos do site — o mesmo comportamento do leitor dentro da app
 * (app/components/ModuleVideoModal.tsx + app/lib/module-videos.ts):
 *  - o nosso cabeçalho (mascote, título, "Vida Diária App") no lugar do título do YouTube;
 *  - sem os controles do YouTube e sem a legenda automática (a legenda já vem na imagem);
 *  - a nossa própria barra de progresso;
 *  - clicar no vídeo pausa e retoma.
 *
 * O truque do título: a caixa do player é mais alta que o vídeo, então o YouTube deixa
 * uma faixa preta em cima (é ali que ele escreve o título e o nome do canal) e outra embaixo.
 * A de cima fica atrás do nosso cabeçalho e a de baixo é cortada pela moldura. */
(function () {
  var players = [];

  function killCaptions(player) {
    try { player.unloadModule('captions'); } catch (e) {}
    try { player.unloadModule('cc'); } catch (e) {}
    try { player.setOption('captions', 'track', {}); } catch (e) {}
    try { player.setOption('cc', 'track', {}); } catch (e) {}
  }

  function setup(root) {
    var videoId = root.getAttribute('data-video');
    var slot = root.querySelector('.player-slot');
    var poster = root.querySelector('.player-poster');
    var clickLayer = root.querySelector('.player-click');
    var fill = root.querySelector('.player-progress > span');
    var state = { player: null, started: false, timer: null };

    function play() {
      poster.classList.add('is-loading');
      if (state.player) {
        state.player.playVideo();
        return;
      }
      state.player = new YT.Player(slot, {
        videoId: videoId,
        width: '100%',
        height: '100%',
        playerVars: {
          rel: 0, playsinline: 1, modestbranding: 1,
          cc_load_policy: 0, iv_load_policy: 3,
          controls: 0, disablekb: 1, fs: 0,
        },
        events: {
          onReady: function (event) {
            killCaptions(event.target);
            event.target.playVideo();
            setTimeout(function () { killCaptions(event.target); }, 1500);
          },
          onStateChange: function (event) {
            if (event.data === YT.PlayerState.PLAYING) {
              killCaptions(event.target);
              root.classList.add('is-playing');
              root.classList.remove('is-ended');
              poster.classList.remove('is-loading');
              if (!state.timer) {
                state.timer = setInterval(function () {
                  var total = event.target.getDuration();
                  if (total > 0) fill.style.width = Math.min(100, (event.target.getCurrentTime() / total) * 100) + '%';
                }, 250);
              }
            }
            if (event.data === YT.PlayerState.ENDED) {
              // No fim o YouTube mostra a tela dele (título, repetir, "Shorts"):
              // volta a capa, agora com o botão de ver de novo.
              root.classList.remove('is-playing');
              root.classList.add('is-ended');
              fill.style.width = '100%';
            }
          },
          onApiChange: function (event) { killCaptions(event.target); },
        },
      });
    }

    // Garantia extra para navegadores sem overflow: clip — se o interior deslocar,
    // volta logo ao topo.
    root.addEventListener('scroll', function () { root.scrollTop = 0; });

    poster.addEventListener('click', play);
    // Clicar no vídeo em andamento pausa ou retoma — o clique fica na nossa camada,
    // e o YouTube nunca o recebe.
    clickLayer.addEventListener('click', function () {
      if (!state.player) return;
      var s = state.player.getPlayerState();
      if (s === YT.PlayerState.PLAYING) state.player.pauseVideo();
      else state.player.playVideo();
    });
    players.push(state);
  }

  window.onYouTubeIframeAPIReady = function () {
    document.querySelectorAll('.player[data-video]').forEach(setup);
  };

  var api = document.createElement('script');
  api.src = 'https://www.youtube.com/iframe_api';
  document.head.appendChild(api);
})();
