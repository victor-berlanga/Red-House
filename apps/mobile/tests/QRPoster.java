import com.google.zxing.*;
import com.google.zxing.qrcode.QRCodeWriter;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.io.File;
public class QRPoster {
 public static void main(String[] args) throws Exception {
  var matrix=new QRCodeWriter().encode(args[0],BarcodeFormat.QR_CODE,1024,1024);
  var image=new BufferedImage(1024,1024,BufferedImage.TYPE_INT_RGB);
  for(int y=0;y<1024;y++)for(int x=0;x<1024;x++)image.setRGB(x,y,matrix.get(x,y)?0x000000:0xffffff);
  ImageIO.write(image,"png",new File(args[1]));
 }
}
