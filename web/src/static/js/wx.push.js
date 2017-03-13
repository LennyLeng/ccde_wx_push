$(document).ready(function()
{
  if ($('html').hasClass('app_list'))
	{
    //检查按钮ajax响应
		$(".btn-check").click(function(){
      check_btn = $(this)
      check_btn.removeClass('btn-success');
      check_btn.removeClass('btn-danger');
      check_btn.addClass('btn-primary');
      var l = Ladda.create(check_btn[0]);
      l.start();
      app_id = check_btn.parent().parent().attr('value');
      $.get("/check/"+app_id,
        function(data){
          l.stop();
          if(data.status == false)
          {
            check_btn.removeClass('btn-primary');
            check_btn.removeClass('btn-success');
            check_btn.addClass('btn-danger');
            check_btn.html('错误');
            $("#show_error_content").html(data.error_info);
            $('#show_error').modal('show');
          }
          else
          {
            check_btn.removeClass('btn-primary');
            check_btn.removeClass('btn-danger');
            check_btn.addClass('btn-success');
            check_btn.html('正常');
          }
        }, 'json');
		});
    //详情按钮小窗口打开
    $(".btn-detail").click(function(){
      app_id = $(this).parent().parent().attr('value');
      window.open (window.location.protocol + '//' +  window.location.host + '/app_detail/' + app_id, "应用详情", "width=800, toolbar=no, menubar=no, scrollbars=yes, resizable=no,location=no, status=no");
    });
  }
})
